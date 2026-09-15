import { CheckCircle2, FileScan, Plus, UploadCloud } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  useActivityDrafts,
  useConfirmOCRDraft,
  useCreateExcelDraft,
  useCreateFacility,
  useCreateOCRDraft,
  useFacilities,
} from "../api/hooks";
import { useAuth } from "../context/AuthContext";

const isExcelFile = (file) => /\.(xlsx|xls)$/i.test(file?.name ?? "");

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => (typeof item === "string" ? item : item?.msg || JSON.stringify(item)))
      .join("; ");
  }
  if (typeof err?.message === "string" && err.message.trim()) return err.message;
  return fallback;
}

function Field({ label, value }) {
  return (
    <div className="rounded-lg border border-line bg-canvas px-4 py-3">
      <div className="text-xs uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 break-all font-mono text-sm text-ink">{value ?? "–"}</div>
    </div>
  );
}

function shortFacility(id) {
  if (!id) return "—";
  return `${id.slice(0, 8)}…`;
}

export default function OCR() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [confirmed, setConfirmed] = useState([]);
  const [currentDrafts, setCurrentDrafts] = useState([]);
  const [view, setView] = useState("current");
  const [facilityId, setFacilityId] = useState("");
  const [newFacilityName, setNewFacilityName] = useState("");

  // Drafts already stored in the backend — the "Saved drafts" history view.
  const draftsQuery = useActivityDrafts();
  const facilitiesQuery = useFacilities();
  const createFacility = useCreateFacility();
  const createDraft = useCreateOCRDraft();
  const createExcelDraft = useCreateExcelDraft();
  const confirmDraft = useConfirmOCRDraft();

  const facilities = facilitiesQuery.data ?? [];
  const savedDrafts = draftsQuery.data ?? [];
  const visibleDrafts = view === "saved" ? savedDrafts : currentDrafts;
  const submitting = createDraft.isPending || createExcelDraft.isPending;

  useEffect(() => {
    if (facilityId || facilities.length === 0) return;
    const preferred = facilities.find((facility) => facility.id === user?.facility_id);
    setFacilityId((preferred ?? facilities[0]).id);
  }, [facilities, facilityId, user?.facility_id]);

  const confirmedByDraft = new Map(confirmed.map((entry) => [entry.draftId, entry.record]));

  const isDraftConfirmed = (draft) =>
    confirmedByDraft.has(draft.id) || draft.status === "confirmed";

  const selected = useMemo(
    () => visibleDrafts.find((draft) => draft.id === selectedId) ?? visibleDrafts[0] ?? null,
    [visibleDrafts, selectedId],
  );

  const allConfirmed = visibleDrafts.length > 0 && visibleDrafts.every(isDraftConfirmed);

  const submitLabel = submitting
    ? isExcelFile(file)
      ? "Ingesting…"
      : "Extracting…"
    : "Create draft";

  const preview = useMemo(() => {
    if (!selected) return null;
    return [
      { label: "Facility", value: selected.facility_id },
      { label: "Status", value: selected.status },
      { label: "Source", value: selected.source_type },
      { label: "Period start", value: new Date(selected.period_start).toLocaleString() },
      { label: "Period end", value: new Date(selected.period_end).toLocaleString() },
      { label: "Activity", value: selected.activity_type },
      { label: "Quantity", value: selected.quantity },
      { label: "Unit", value: selected.unit },
    ];
  }, [selected]);

  async function handleUpload(event) {
    event.preventDefault();
    setError("");
    setSelectedId(null);
    setConfirmed([]);
    setCurrentDrafts([]);
    if (!file) {
      setError("Choose a file first.");
      return;
    }
    const excel = isExcelFile(file);
    if (excel && !facilityId) {
      setError("Choose or create a facility before ingesting an Excel workbook.");
      return;
    }
    try {
      const result = excel
        ? await createExcelDraft.mutateAsync({ file, facilityId })
        : await createDraft.mutateAsync(file);
      setCurrentDrafts(result ?? []);
      setView("current");
      if ((result ?? []).length === 0) {
        setError("No new drafts — these rows are already ingested.");
      }
      await draftsQuery.refetch();
    } catch (err) {
      setError(
        messageFromError(
          err,
          excel ? "Failed to ingest Excel workbook." : "Failed to extract OCR drafts.",
        ),
      );
    }
  }

  async function handleCreateFacility(event) {
    event.preventDefault();
    const name = newFacilityName.trim();
    if (!name) {
      setError("Facility name is required.");
      return;
    }
    setError("");
    try {
      const facility = await createFacility.mutateAsync({ name });
      await facilitiesQuery.refetch();
      setFacilityId(facility.id);
      setNewFacilityName("");
    } catch (err) {
      setError(messageFromError(err, "Failed to create facility."));
    }
  }

  async function handleConfirm() {
    if (!selected?.id || isDraftConfirmed(selected)) return;
    setError("");
    try {
      const record = await confirmDraft.mutateAsync(selected.id);
      const confirmedId = selected.id;
      setConfirmed((prev) => [...prev, { draftId: confirmedId, record }]);
      const next = visibleDrafts.find(
        (draft) => draft.id !== confirmedId && !isDraftConfirmed(draft),
      );
      setSelectedId(next?.id ?? null);
      await draftsQuery.refetch();
    } catch (err) {
      setError(messageFromError(err, "Failed to confirm OCR draft."));
    }
  }

  async function openSaved() {
    setView("saved");
    setSelectedId(null);
    await draftsQuery.refetch();
  }

  function reset() {
    setFile(null);
    setSelectedId(null);
    setConfirmed([]);
    setCurrentDrafts([]);
    setView("current");
    createDraft.reset();
    createExcelDraft.reset();
    confirmDraft.reset();
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">OCR Intake</h1>
        <p className="text-sm text-muted">
          Upload a scanned bill, PDF, image, CSV, or Excel sheet, review the extracted fields,
          then confirm.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-card border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#E8F3EC]">
              <UploadCloud size={18} className="text-leaf" />
            </div>
            <div>
              <div className="font-semibold text-ink">Upload document</div>
              <div className="text-sm text-muted">
                PDF, image, CSV, or Excel files work best here.
              </div>
            </div>
          </div>

          <form onSubmit={handleUpload} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="facility" className="text-xs font-semibold uppercase tracking-wider text-muted">
                Facility
              </label>
              {facilities.length > 0 ? (
                <select
                  id="facility"
                  value={facilityId}
                  onChange={(e) => setFacilityId(e.target.value)}
                  className="w-full rounded-xl border border-line bg-canvas px-3 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-leaf/40"
                >
                  {facilities.map((facility) => (
                    <option key={facility.id} value={facility.id}>
                      {facility.name}
                      {facility.location ? ` — ${facility.location}` : ""}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="text-sm text-muted">No facilities yet — create one below.</div>
              )}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={newFacilityName}
                onChange={(e) => setNewFacilityName(e.target.value)}
                placeholder="Add a facility…"
                className="w-full rounded-xl border border-line bg-canvas px-3 py-2.5 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-leaf/40"
              />
              <button
                type="button"
                onClick={handleCreateFacility}
                disabled={createFacility.isPending}
                className="inline-flex shrink-0 items-center gap-1 rounded-xl border border-line bg-white px-3 py-2.5 text-sm font-semibold text-ink hover:bg-canvas disabled:opacity-60"
              >
                <Plus size={15} />
                {createFacility.isPending ? "Adding…" : "Add"}
              </button>
            </div>
            {isExcelFile(file) && (
              <p className="rounded-lg border border-[#FDE8D7] bg-[#FFF6ED] px-3 py-2 text-xs text-[#9A5B13]">
                Excel workbook detected — it will be ingested as electricity drafts for the
                selected facility.
              </p>
            )}

            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.csv,.xlsx,.txt,application/pdf,image/*,text/csv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-muted file:mr-4 file:rounded-xl file:border-0 file:bg-leaf file:px-4 file:py-2.5 file:text-sm file:font-semibold file:text-white hover:file:bg-leaf-hover"
            />

            <button
              type="submit"
              disabled={submitting || (isExcelFile(file) && !facilityId)}
              className="rounded-xl bg-leaf py-3.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
            >
              {submitLabel}
            </button>
          </form>

          {error && <p className="mt-4 text-sm text-rose">{error}</p>}
        </div>

        <div className="rounded-card border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#E8F3EC]">
              <FileScan size={18} className="text-leaf" />
            </div>
            <div>
              <div className="font-semibold text-ink">Drafts</div>
              <div className="text-sm text-muted">Review new uploads or browse saved drafts.</div>
            </div>
          </div>
          <div className="mt-3 flex gap-1 rounded-xl border border-line bg-canvas p-1">
            <button
              type="button"
              onClick={() => {
                setView("current");
                setSelectedId(null);
              }}
              className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                view === "current" ? "bg-white text-ink shadow-sm" : "text-muted hover:text-ink"
              }`}
            >
              Current upload
            </button>
            <button
              type="button"
              onClick={openSaved}
              className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                view === "saved" ? "bg-white text-ink shadow-sm" : "text-muted hover:text-ink"
              }`}
            >
              Saved drafts
            </button>
          </div>

          {visibleDrafts.length === 0 ? (
          <div className="grid h-[240px] place-items-center rounded-lg border border-dashed border-line text-sm text-muted">
            {view === "saved"
              ? draftsQuery.isLoading
                ? "Loading saved drafts…"
                : "No saved drafts yet"
              : "Upload a document to review its drafts."}
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {allConfirmed && (
              <div className="flex items-center justify-between rounded-lg border border-[#CFE8D8] bg-[#F2FAF5] px-3 py-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-leaf-deep">
                  <CheckCircle2 size={15} />
                  All {visibleDrafts.length} draft
                  {visibleDrafts.length === 1 ? "" : "s"} confirmed
                </div>
                {view === "current" && (
                  <button
                    onClick={reset}
                    className="text-xs font-semibold text-ink underline-offset-2 hover:underline"
                  >
                    Upload another
                  </button>
                )}
              </div>
            )}
            <div className="max-h-40 divide-y divide-line overflow-y-auto rounded-lg border border-line">
              {visibleDrafts.map((draft, index) => {
                const isConfirmed = isDraftConfirmed(draft);
                const isActive = selected?.id === draft.id;
                return (
                  <button
                    key={draft.id}
                    type="button"
                    onClick={() => setSelectedId(draft.id)}
                    className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors ${
                      isActive ? "bg-canvas" : "hover:bg-canvas"
                    }`}
                  >
                    <span className="font-mono text-xs text-muted">{index + 1}</span>
                    <span className="font-semibold capitalize text-ink">{draft.activity_type}</span>
                    <span className="text-body">
                      {draft.quantity} {draft.unit}
                    </span>
                    <span className="ml-auto font-mono text-xs text-muted">
                      {shortFacility(draft.facility_id)}
                    </span>
                    {isConfirmed ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-leaf-deep">
                        <CheckCircle2 size={12} /> Confirmed
                      </span>
                    ) : (
                      <span className={`text-xs ${isActive ? "font-semibold text-leaf" : "text-muted"}`}>
                        {isActive ? "Reviewing" : "Review"}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>

    {selected && (
      <div className="rounded-card border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#E8F3EC]">
            <FileScan size={18} className="text-leaf" />
          </div>
          <div>
            <div className="font-semibold text-ink">Review draft</div>
            <div className="text-sm text-muted">
              {selected.activity_type} for {shortFacility(selected.facility_id)} — verify and confirm
              to add it to Activity Records.
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {preview?.map((field) => (
              <Field key={field.label} label={field.label} value={field.value} />
            ))}
          </div>
          <button
            onClick={handleConfirm}
            disabled={confirmDraft.isPending || isDraftConfirmed(selected)}
            className="rounded-xl bg-leaf py-3.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
          >
            {isDraftConfirmed(selected)
              ? "Confirmed"
              : confirmDraft.isPending
                ? "Confirming…"
                : "Confirm draft"}
          </button>
        </div>
      </div>
    )}
    </div>
  );
}