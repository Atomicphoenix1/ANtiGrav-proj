"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAdminCombo } from "../hooks/useAdminCombo";

export default function AdminControlPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [assets, setAssets] = useState<{ mp3s: string[]; srts: string[] }>({ mp3s: [], srts: [] });

  const [mp3File, setMp3File] = useState<File | null>(null);
  const [srtFile, setSrtFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState({ bookTitle: "", sheikhName: "", yearDate: "", youtubeUrl: "" });

  const { isChordActive } = useAdminCombo(() => setIsOpen(true));

  const fetchAssets = useCallback(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/admin/assets");
      const data = await res.json();
      setAssets(data);
    } catch {
      setAssets({ mp3s: [], srts: [] });
    }
  }, []);

  useEffect(() => {
    if (isOpen) fetchAssets();
  }, [isOpen, fetchAssets]);

  const handleUpload = async (overwriteConfirmed = false) => {
    if (!mp3File || !srtFile) return alert("Both MP3 and SRT assets must be mapped simultaneously.");

    const formData = new FormData();
    formData.append("mp3", mp3File);
    formData.append("srt", srtFile);
    formData.append("book_title", metadata.bookTitle);
    formData.append("sheikh_name", metadata.sheikhName);
    formData.append("year_date", metadata.yearDate);
    formData.append("youtube_url", metadata.youtubeUrl);
    formData.append("overwrite", String(overwriteConfirmed));

    const res = await fetch("http://127.0.0.1:8000/api/admin/upload", {
      method: "POST",
      body: formData,
    });

    if (res.status === 409) {
      const confirmOverwrite = window.confirm("File collision detected! Do you grant permission to overwrite this file asset layout?");
      if (confirmOverwrite) handleUpload(true);
    } else if (res.ok) {
      alert("Injected successfully!");
      fetchAssets();
    } else {
      alert("Upload pipeline failure.");
    }
  };

  const handleDelete = async (type: "mp3" | "srt", filename: string) => {
    if (!window.confirm(`Are you sure you want to completely erase ${filename}?`)) return;
    await fetch(`http://127.0.0.1:8000/api/admin/assets/${type}/${encodeURIComponent(filename)}`, { method: "DELETE" });
    fetchAssets();
  };

  const handleNuclearFlush = async () => {
    const firstVerify = window.confirm("WARNING: You are triggering a structural database reset. This deletes all shards, metrics, and text arrays. Proceed?");
    if (!firstVerify) return;
    const finalVerify = window.prompt("Type 'FLUSH' to confirm immediate database destruction:");
    if (finalVerify !== "FLUSH") return alert("Mismatch. Aborted.");

    const res = await fetch("http://127.0.0.1:8000/api/admin/flush", { method: "POST" });
    if (res.ok) alert("Database wiped clean.");
    window.location.reload();
  };

  return (
    <>
      {isChordActive && !isOpen && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-black text-green-400 border border-green-500 font-mono text-xs px-4 py-2 rounded shadow-2xl animate-pulse z-50">
          :: SECURE ACCESS SIGNAL ENGAGED ... ENTER AUTHENTICATION CODE SEQUENCE ::
        </div>
      )}

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center p-6 z-50 font-sans text-slate-100">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-4xl w-full p-6 max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-700 pb-4 mb-6">
              <h2 className="text-xl font-bold font-mono tracking-wider text-green-400">CENTRAL CONTROL INFRASTRUCTURE PANEL</h2>
              <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white font-mono font-bold">ESC[X]</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                <h3 className="font-semibold mb-3 text-sm tracking-wide text-slate-300 uppercase">Dual Asset Ingestion Pipeline</h3>
                <label className="block text-xs text-slate-400 mb-1">Select Audio Source (MP3):</label>
                <input type="file" accept=".mp3" onChange={e => setMp3File(e.target.files?.[0] || null)} className="w-full text-xs text-slate-300 mb-3 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-700 file:text-slate-200" />

                <label className="block text-xs text-slate-400 mb-1">Select Subtitle Map (SRT):</label>
                <input type="file" accept=".srt" onChange={e => setSrtFile(e.target.files?.[0] || null)} className="w-full text-xs text-slate-300 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-700 file:text-slate-200" />
              </div>

              <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                <h3 className="font-semibold mb-3 text-sm tracking-wide text-slate-300 uppercase">Search Filter Attribute Mapping</h3>
                <input type="text" placeholder="Book Title (e.g. الرسالة التبوكية)" value={metadata.bookTitle} onChange={e => setMetadata({ ...metadata, bookTitle: e.target.value })} className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm mb-2" />
                <input type="text" placeholder="Sheikh Name (e.g. ابن القيم)" value={metadata.sheikhName} onChange={e => setMetadata({ ...metadata, sheikhName: e.target.value })} className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm mb-2" />
                <input type="text" placeholder="Year / Production Date" value={metadata.yearDate} onChange={e => setMetadata({ ...metadata, yearDate: e.target.value })} className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm mb-2" />
                <input type="text" placeholder="YouTube Video URL (Optional)" value={metadata.youtubeUrl} onChange={e => setMetadata({ ...metadata, youtubeUrl: e.target.value })} className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm mb-4" />
                <button onClick={() => handleUpload(false)} className="w-full bg-green-600 hover:bg-green-700 transition text-white font-semibold rounded p-2 text-sm">ENGAGE INGESTION PIPE</button>
              </div>
            </div>

            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 mb-6">
              <h3 className="font-semibold mb-3 text-sm text-slate-300 uppercase">Current Storage Inventory</h3>
              <div className="grid grid-cols-2 gap-4 max-h-40 overflow-y-auto pr-2">
                <div>
                  <h4 className="text-xs text-slate-400 font-mono mb-1">Available MP3s:</h4>
                  {assets.mp3s.map(m => (
                    <div key={m} className="flex justify-between items-center text-xs bg-slate-950 p-1.5 rounded mb-1 border border-slate-800">
                      <span className="truncate max-w-[80%]">{m}</span>
                      <button onClick={() => handleDelete("mp3", m)} className="text-red-400 hover:text-red-600 font-bold px-1">X</button>
                    </div>
                  ))}
                </div>
                <div>
                  <h4 className="text-xs text-slate-400 font-mono mb-1">Available SRTs:</h4>
                  {assets.srts.map(s => (
                    <div key={s} className="flex justify-between items-center text-xs bg-slate-950 p-1.5 rounded mb-1 border border-slate-800">
                      <span className="truncate max-w-[80%]">{s}</span>
                      <button onClick={() => handleDelete("srt", s)} className="text-red-400 hover:text-red-600 font-bold px-1">X</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="border-t border-slate-700 pt-4 flex justify-between items-center">
              <span className="text-xs text-slate-500 font-mono">System Integrity Hook: Active</span>
              <button onClick={handleNuclearFlush} className="bg-red-900 border border-red-600 text-red-200 hover:bg-red-700 font-mono text-xs font-bold px-4 py-2 rounded transition">NUCLEAR FLUSH DATABASE</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
