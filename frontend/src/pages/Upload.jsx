import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Upload, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import client from "../api/client";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState(null);

  const { mutate, isPending } = useMutation({
    mutationFn: async (f) => {
      const fd = new FormData();
      fd.append("file", f);
      const { data } = await client.post("/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: (d) => setMsg({ type: "ok", text: `Uploaded ${d.row_count} rows` }),
    onError: (e) => setMsg({ type: "err", text: e.response?.data?.detail || "Upload failed" }),
  });

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-2xl font-bold">Upload Energy Data</h1>
      <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
        <label className="flex h-40 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 transition-colors hover:border-[#4CAF50]">
          <Upload className="mb-2 text-4xl text-gray-400" />
          <span className="text-gray-600">Drag &amp; drop .xlsx or .csv</span>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => {
              setFile(e.target.files[0]);
              setMsg(null);
            }}
            className="hidden"
          />
        </label>
        {file && (
          <p className="truncate text-sm text-gray-500">{file.name}</p>
        )}
        <button
          onClick={() => file && mutate(file)}
          disabled={!file || isPending}
          className="w-full rounded-xl bg-[#4CAF50] py-3 font-bold text-white transition-colors hover:bg-[#43a047] disabled:opacity-60"
        >
          {isPending ? <Loader2 className="mx-auto h-5 w-5 animate-spin" /> : "Upload"}
        </button>
        {msg && (
          <div
            className={`rounded-lg p-3 text-sm ${
              msg.type === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
            }`}
          >
            {msg.type === "ok" ? (
              <CheckCircle className="mr-1 inline h-4 w-4" />
            ) : (
              <AlertCircle className="mr-1 inline h-4 w-4" />
            )}
            {msg.text}
          </div>
        )}
      </div>
    </div>
  );
}
