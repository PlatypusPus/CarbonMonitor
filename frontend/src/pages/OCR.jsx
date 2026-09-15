import { CheckCircle2, FileScan, UploadCloud } from "lucide-react";
import { useMemo, useState } from "react";

import { useConfirmOCRDraft, useCreateOCRDraft } from "../api/hooks";

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

export default function OCR() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(null);

  const createDraft = useCreateOCRDraft();
  const confirmDraft = useConfirmOCRDraft();
  const draft = createDraft.data;

  const preview = useMemo(() => {
    if (!draft) return null;
    return [
      { label: "Facility", value: draft.facility_id },
      { label: "Period start", value: new Date(draft.period_start).toLocaleString() },
      { label: "Period end", value: new Date(draft.period_end).toLocaleString() },
      { label: "Activity", value: draft.activity_type },
      { label: "Quantity", value: draft.quantity },
      { label: "Unit", value: draft.unit },
    ];
  }, [draft]);

  async function handleUpload(event) {
    event.preventDefault();
    setError("");
    setConfirmed(null);
    if (!file) {
      setError("Choose a file first.");
      return;
    }
    try {
      await createDraft.mutateAsync(file);
    } catch (err) {
      setError(messageFromError(err, "Failed to extract OCR draft."));
    }
  }

  async function handleConfirm() {
    if (!draft?.id) return;
    setError("");
    try {
      const record = await confirmDraft.mutateAsync(draft.id);
      setConfirmed(record);
    } catch (err) {
      setError(messageFromError(err, "Failed to confirm OCR draft."));
    }
  }

  function reset() {
    setFile(null);
    setConfirmed(null);
    createDraft.reset();
    confirmDraft.reset();
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">OCR Intake</h1>
        <p className="text-sm text-muted">
          Upload a scanned bill or text bill, review the extracted fields, then confirm it.
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
                PDF, PNG, JPG, WEBP, or text files work best here.
              </div>
            </div>
          </div>

          <form onSubmit={handleUpload} className="flex flex-col gap-4">
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,application/pdf,image/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-muted file:mr-4 file:rounded-xl file:border-0 file:bg-leaf file:px-4 file:py-2.5 file:text-sm file:font-semibold file:text-white hover:file:bg-leaf-hover"
            />

            <button
              type="submit"
              disabled={createDraft.isPending}
              className="rounded-xl bg-leaf py-3.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
            >
              {createDraft.isPending ? "Extracting…" : "Create draft"}
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
              <div className="font-semibold text-ink">Review draft</div>
              <div className="text-sm text-muted">OCR output stays pending until confirmed.</div>
            </div>
          </div>

          {!draft && !confirmed ? (
            <div className="grid h-[240px] place-items-center rounded-lg border border-dashed border-line text-sm text-muted">
              No OCR draft yet
            </div>
          ) : confirmed ? (
            <div className="flex h-[240px] flex-col justify-between rounded-lg border border-[#CFE8D8] bg-[#F2FAF5] p-4">
              <div className="flex items-center gap-2 text-leaf-deep">
                <CheckCircle2 size={18} />
                <span className="font-semibold">Confirmed</span>
              </div>
              <div className="space-y-2 text-sm text-body">
                <div>Activity record created successfully.</div>
                <div className="break-all font-mono text-xs text-muted">{confirmed.id}</div>
              </div>
              <button
                onClick={reset}
                className="self-start rounded-lg border border-line bg-white px-4 py-2 text-sm font-semibold text-ink hover:bg-canvas"
              >
                Upload another
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {preview?.map((field) => (
                  <Field key={field.label} label={field.label} value={field.value} />
                ))}
              </div>
              <button
                onClick={handleConfirm}
                disabled={confirmDraft.isPending}
                className="rounded-xl bg-leaf py-3.5 font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
              >
                {confirmDraft.isPending ? "Confirming…" : "Confirm draft"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
