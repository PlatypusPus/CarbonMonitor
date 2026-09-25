import { AlertCircle, CheckCircle, CheckCircle2, FileScan, Loader2, Plus, UploadCloud } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import client from "../api/client";
import {
  useActivityDrafts,
  useConfirmOCRDraft,
  useCreateFacility,
  useFacilities,
  useRejectOCRDraft,
} from "../api/hooks";
import { useAuth } from "../context/AuthContext";

const SPREADSHEET = /\.(csv|xlsx)$/i;
const ACCEPT = ".csv,.xlsx,.pdf,.png,.jpg,.jpeg,.webp,.txt,application/pdf,image/*,text/csv";

const isSpreadsheet = (file) => SPREADSHEET.test(file?.name ?? "");

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

async function fetchPreview(file, facilityId) {
  const fd = new FormData();
  fd.append("file", file);
  if (facilityId) fd.append("facility_id", facilityId);
  const { data } = await client.post("/upload/preview", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

function Field({ label, value }) {
  return (
    <div className="rounded-lg border border-line bg-canvas px-4 py-3">
      <div className="text-xs uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 break-all font-mono text-sm text-ink">{value ?? "–"}</div>
    </div>
  );
}

function getFacilityName(facilities, facilityId) {
  if (!facilityId) return "—";
  const facility = facilities.find((f) => f.id === facilityId);
  return facility?.name ?? "—";
}

export default function Intake() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewError, setPreviewError] = useState(null);
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [confirmed, setConfirmed] = useState([]);
  const [rejected, setRejected] = useState([]);
  const [currentDrafts, setCurrentDrafts] = useState([]);
  const [view, setView] = useState("saved");
  const [facilityId, setFacilityId] = useState("");
  const [newFacilityName, setNewFacilityName] = useState("");

  const draftsQuery = useActivityDrafts();
  const facilitiesQuery = useFacilities();
  const createFacility = useCreateFacility();
  const confirmDraft = useConfirmOCRDraft();
  const rejectDraft = useRejectOCRDraft();

  const facilities = facilitiesQuery.data ?? [];
  const savedDrafts = draftsQuery.data ?? [];
  const visibleDrafts = (view === "saved" ? savedDrafts : currentDrafts).filter(
    (draft) => !rejected.includes(draft.id),
  );

  useEffect(() => {
    if (facilityId || facilities.length === 0) return;
    const preferred = facilities.find((facility) => facility.id === user?.facility_id);
    if (preferred) setFacilityId(preferred.id);
  }, [facilities, facilityId, user?.facility_id]);

  const upload = useMutation({
    mutationFn: async (f) => {
      const spreadsheet = isSpreadsheet(f);
      const fd = new FormData();
      fd.append("file", f);
      if (facilityId) fd.append("facility_id", facilityId);
      const { data } = await client.post(spreadsheet ? "/upload" : "/activity/ocr", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return { data, spreadsheet };
    },
    onSuccess: async ({ data, spreadsheet }) => {
      const before = new Set(savedDrafts.map((draft) => draft.id));
      const staged = spreadsheet ? data.row_count : (data?.length ?? 0);
      const fresh = await draftsQuery.refetch();
      const created = (fresh.data ?? []).filter((draft) => !before.has(draft.id));
      setCurrentDrafts(created);
      setView(created.length > 0 ? "current" : "saved");
      setSelectedId(null);
      setConfirmed([]);
      setMsg({
        type: staged > 0 ? "ok" : "info",
        text:
          staged > 0
            ? `${staged} row${staged === 1 ? "" : "s"} staged for review — confirm them below to add them to your emissions.`
            : "No new rows — this file is already ingested.",
      });
    },
    onError: (err) => {
      setMsg({ type: "err", text: messageFromError(err, "Upload failed.") });
    },
  });

  useEffect(() => {
    setPreview(null);
    setPreviewError(null);
    setMsg(null);
    if (!file || !isSpreadsheet(file)) return;
    let cancelled = false;
    setPreview("loading");
    fetchPreview(file, facilityId)
      .then((data) => {
        if (!cancelled) setPreview(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setPreview(null);
        setPreviewError(err.response?.data?.detail || err.message || "Could not preview this file.");
      });
    return () => {
      cancelled = true;
    };
  }, [file, facilityId]);

  const confirmedByDraft = new Map(confirmed.map((entry) => [entry.draftId, entry.record]));

  const isDraftConfirmed = (draft) =>
    confirmedByDraft.has(draft.id) || draft.status === "confirmed";

  const selected = useMemo(
    () => visibleDrafts.find((draft) => draft.id === selectedId) ?? visibleDrafts[0] ?? null,
    [visibleDrafts, selectedId],
  );

  const allConfirmed = visibleDrafts.length > 0 && visibleDrafts.every(isDraftConfirmed);

  const previewFields = useMemo(() => {
    if (!selected) return null;
    return [
      { label: "Facility", value: getFacilityName(facilities, selected.facility_id) },
      { label: "Status", value: selected.status },
      { label: "Source", value: selected.source_type },
      { label: "Period start", value: new Date(selected.period_start).toLocaleString() },
      { label: "Period end", value: new Date(selected.period_end).toLocaleString() },
      { label: "Activity", value: selected.activity_type },
      { label: "Quantity", value: selected.quantity },
      { label: "Unit", value: selected.unit },
    ];
  }, [selected, facilities]);

  function handleFile(f) {
    setFile(f ?? null);
    setError("");
  }

  async function handleUpload(event) {
    event.preventDefault();
    setError("");
    setMsg(null);
    if (!file) {
      setError("Choose a file first.");
      return;
    }
    if (facilities.length > 0 && !facilityId) {
      setError("Choose a facility first.");
      return;
    }
    upload.mutate(file);
  }

  function handleDrop(event) {
    event.preventDefault();
    handleFile(event.dataTransfer.files?.[0]);
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
      setError(messageFromError(err, "Failed to confirm draft."));
    }
  }

  async function handleReject() {
    if (!selected?.id || isDraftConfirmed(selected)) return;
    setError("");
    try {
      await rejectDraft.mutateAsync(selected.id);
      const rejectedId = selected.id;
      setRejected((prev) => [...prev, rejectedId]);
      const next = visibleDrafts.find(
        (draft) => draft.id !== rejectedId && !isDraftConfirmed(draft),
      );
      setSelectedId(next?.id ?? null);
      await draftsQuery.refetch();
    } catch (err) {
      setError(messageFromError(err, "Failed to discard draft."));
    }
  }

  function reset() {
    setFile(null);
    setPreview(null);
    setPreviewError(null);
    setMsg(null);
    setError("");
    setSelectedId(null);
    setConfirmed([]);
    setCurrentDrafts([]);
    setView("saved");
    upload.reset();
  }

  const spreadsheet = isSpreadsheet(file);
  const submitting = upload.isPending;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Data Intake</h1>
        <p className="text-sm text-muted">
          Upload a CSV or Excel sheet, or scan a paper bill (PDF or photo). Review every staged
          row here, then confirm it into your emissions.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-card border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#E8F3EC]">
              <UploadCloud size={18} className="text-leaf" />
            </div>
            <div>
              <div className="font-semibold text-ink">Upload a file</div>
              <div className="text-sm text-muted">
                CSV, Excel (.xlsx), PDF, or images. Previewed before staging.
              </div>
            </div>
          </div>

          <form onSubmit={handleUpload} className="flex flex-col gap-4">
            <label
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              className="flex h-36 cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-line bg-canvas transition-colors hover:border-leaf"
            >
              <UploadCloud className="text-3xl text-muted" />
              <span className="text-sm text-muted">
                {file ? file.name : "Click to choose, or drag a file here"}
              </span>
              <input
                type="file"
                accept={ACCEPT}
                onChange={(event) => handleFile(event.target.files?.[0])}
                className="hidden"
              />
            </label>

            <div className="flex flex-col gap-2">
              <label
                htmlFor="facility"
                className="text-xs font-semibold uppercase tracking-wider text-muted"
              >
                Facility
              </label>
              {facilities.length > 0 ? (
                <select
                  id="facility"
                  value={facilityId}
                  onChange={(event) => setFacilityId(event.target.value)}
                  className="w-full rounded-xl border border-line bg-canvas px-3 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-leaf/40"
                >
                  <option value="">Select a facility…</option>
                  {facilities.map((facility) => (
                    <option key={facility.id} value={facility.id}>
                      {facility.name}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="text-sm text-muted">No facilities yet — create one below.</div>
              )}
              <p className="text-xs text-muted">
                {spreadsheet
                  ? "Rows in this file are staged under the selected facility."
                  : "Applied to the scanned document — it overrides any facility printed on the bill."}
              </p>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={newFacilityName}
                onChange={(event) => setNewFacilityName(event.target.value)}
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

            <button
              type="submit"
              disabled={!file || submitting || (facilities.length > 0 && !facilityId)}
              className="rounded-xl bg-leaf py-3.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
            >
              {submitting ? (
                <Loader2 className="mx-auto h-5 w-5 animate-spin" />
              ) : spreadsheet ? (
                "Upload"
              ) : (
                "Scan & extract"
              )}
            </button>
          </form>

          {preview === "loading" && (
            <p className="mt-3 flex items-center gap-2 text-sm text-muted">
              <Loader2 className="h-4 w-4 animate-spin" /> Previewing file…
            </p>
          )}

          {previewError && (
            <div className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
              <AlertCircle className="mr-1 inline h-4 w-4" /> {previewError}
            </div>
          )}

          {preview && preview !== "loading" && (
            <div className="mt-3">
              <p className="mb-2 text-sm text-muted">
                {preview.columns.length} columns · {preview.row_count} row
                {preview.row_count === 1 ? "" : "s"}
                {preview.row_count > preview.rows.length
                  ? ` · showing first ${preview.rows.length}`
                  : ""}
              </p>
              <div className="max-h-56 overflow-auto rounded-lg border border-line">
                <table className="w-full border-collapse text-xs">
                  <thead>
                    <tr className="bg-canvas text-left uppercase tracking-wider text-muted">
                      {preview.columns.map((column) => (
                        <th
                          key={column}
                          className="whitespace-nowrap border-b border-line px-3 py-2 font-semibold"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-canvas">
                        {row.map((cell, cellIndex) => (
                          <td
                            key={cellIndex}
                            className="whitespace-nowrap border-b border-line px-3 py-2 font-mono text-body"
                          >
                            {cell ?? "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {msg && (
            <div
              className={`mt-3 rounded-lg p-3 text-sm ${
                msg.type === "err"
                  ? "bg-rose-50 text-rose-700"
                  : msg.type === "ok"
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-canvas text-body"
              }`}
            >
              {msg.type === "err" ? (
                <AlertCircle className="mr-1 inline h-4 w-4" />
              ) : (
                <CheckCircle className="mr-1 inline h-4 w-4" />
              )}
              {msg.text}
            </div>
          )}

          {error && <p className="mt-3 text-sm text-rose">{error}</p>}
        </div>

        <div className="rounded-card border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#E8F3EC]">
              <FileScan size={18} className="text-leaf" />
            </div>
            <div>
              <div className="font-semibold text-ink">Drafts</div>
              <div className="text-sm text-muted">
                Nothing reaches your emissions until you confirm it.
              </div>
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
              onClick={() => {
                setView("saved");
                setSelectedId(null);
                draftsQuery.refetch();
              }}
              className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                view === "saved" ? "bg-white text-ink shadow-sm" : "text-muted hover:text-ink"
              }`}
            >
              Saved drafts
            </button>
          </div>

          {visibleDrafts.length === 0 ? (
            <div className="mt-3 grid h-[240px] place-items-center rounded-lg border border-dashed border-line text-sm text-muted">
              {view === "saved"
                ? draftsQuery.isLoading
                  ? "Loading saved drafts…"
                  : "No saved drafts yet"
                : "Nothing staged from this upload — the rows may already be ingested."}
            </div>
          ) : (
            <div className="mt-3 flex flex-col gap-4">
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
              <div className="max-h-64 divide-y divide-line overflow-y-auto rounded-lg border border-line">
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
                      <span className="font-semibold capitalize text-ink">
                        {draft.activity_type}
                      </span>
                      <span className="text-body">
                        {draft.quantity} {draft.unit}
                      </span>
                      <span className="ml-auto font-mono text-xs text-muted">
                        {getFacilityName(facilities, draft.facility_id)}
                      </span>
                      {isConfirmed ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-leaf-deep">
                          <CheckCircle2 size={12} /> Confirmed
                        </span>
                      ) : (
                        <span
                          className={`text-xs ${isActive ? "font-semibold text-leaf" : "text-muted"}`}
                        >
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
                {selected.activity_type} for {getFacilityName(facilities, selected.facility_id)} — verify and
                confirm to add it to Activity Records.
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {previewFields?.map((field) => (
                <Field key={field.label} label={field.label} value={field.value} />
              ))}
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <button
                onClick={handleConfirm}
                disabled={confirmDraft.isPending || isDraftConfirmed(selected)}
                className="flex-1 rounded-xl bg-leaf py-3.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
              >
                {isDraftConfirmed(selected)
                  ? "Confirmed"
                  : confirmDraft.isPending
                    ? "Confirming…"
                    : "Confirm draft"}
              </button>
              <button
                onClick={handleReject}
                disabled={rejectDraft.isPending || isDraftConfirmed(selected)}
                title="Discard this row without adding it to the ledger"
                className="rounded-xl border border-line bg-white px-5 py-3.5 font-bold text-muted transition-colors hover:border-rose/40 hover:text-rose disabled:opacity-60"
              >
                {rejectDraft.isPending ? "Discarding…" : "Discard"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
