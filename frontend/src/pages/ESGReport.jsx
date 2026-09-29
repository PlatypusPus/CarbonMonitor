import { FileText } from "lucide-react";
import { useState } from "react";

import client from "../api/client";
import { useWorkspace } from "../context/WorkspaceContext";

export default function ESGReport() {
  const { facilityId } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function downloadReport() {
    setError("");
    setLoading(true);
    try {
      const res = await client.get("/reports/esg", { responseType: "blob", params: { facility_id: facilityId || undefined } });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "carbontrace-esg-report.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to generate the report. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">ESG Report</h1>
        <p className="text-sm text-muted">Generate and download an emissions summary PDF</p>
      </div>

      <div className="flex max-w-md flex-col items-center gap-6 rounded-card border border-line bg-surface p-8 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#E8F3EC]">
          <FileText size={28} className="text-leaf" />
        </div>
        <div>
          <p className="font-semibold text-ink">CarbonTrace ESG Report</p>
          <p className="mt-1 text-sm text-muted">
            Includes Scope 1 and Scope 2 totals, facility comparisons, reporting periods,
            activity calculations, and data quality notes. Pending drafts are excluded.
          </p>
        </div>
        {error && <p className="text-sm text-rose">{error}</p>}
        <button
          onClick={downloadReport}
          disabled={loading}
          className="w-full rounded-xl bg-leaf py-3.5 text-base font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
        >
          {loading ? "Generating…" : "Download PDF"}
        </button>
        <p className="text-xs text-muted">PDF generation may take a few seconds</p>
      </div>
    </div>
  );
}
