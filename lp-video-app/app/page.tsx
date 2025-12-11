"use client";

import { useState, type ChangeEvent } from "react";
import axios from "axios";
import { Upload, FileVideo, Download, Scan, Loader2, Zap } from "lucide-react";

interface DetectedCar {
  car_id: number;
  plate: string;
}

export default function HomePage() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [detectedCars, setDetectedCars] = useState<DetectedCar[]>([]);
  const [downloadUrl, setDownloadUrl] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("");

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      setVideoFile(e.target.files[0]);
      setDetectedCars([]);
      setDownloadUrl("");
      setSessionId("");
    }
  };

  const handleUpload = async () => {
    if (!videoFile) return alert("Please select a video!");

    const formData = new FormData();
    formData.append("file", videoFile);

    try {
      setUploading(true);

      const res = await axios.post<{
        message: string;
        count: number;
        cars: DetectedCar[];
        session_id: string;
        download_url: string;
      }>("http://localhost:8000/api/detect-plate-video", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = res.data;

      if (data.cars && Array.isArray(data.cars)) {
        setDetectedCars(data.cars);
      }

      setDownloadUrl(`http://localhost:8000/download-video/${data.session_id}`);
      setSessionId(data.session_id);
    } catch (err) {
      console.error(err);
      alert("Error uploading or processing video.");
    } finally {
      setUploading(false);
    }
  };

  // Optional: fetch latest info from backend if page reloads
  const fetchVideoInfo = async (sid: string) => {
    try {
      const res = await axios.get<{ session_id: string; cars: DetectedCar[] }>(
        `http://localhost:8000/api/get-video-info/${sid}`
      );
      if (res.data.cars) {
        setDetectedCars(res.data.cars);
        setDownloadUrl(`http://localhost:8000/download-video/${sid}`);
      }
    } catch (err) {
      console.error("Failed to fetch session info", err);
    }
  };

  // If session exists but page reloads, fetch info
  if (sessionId && detectedCars.length === 0) {
    fetchVideoInfo(sessionId);
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan-500/20 blur-lg rounded-lg" />
              <div className="relative p-2.5 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20">
                <Scan className="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <span className="text-xl font-bold text-white tracking-tight">
                PlateVision
              </span>
              <span className="text-xs text-slate-500 ml-2 font-medium">
                PRO
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <span>System Online</span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto px-6 py-12 w-full">
        {/* Hero Section */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-cyan-400 text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            AI-Powered Detection
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">
            License Plate{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
              Detection
            </span>
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Upload your video footage and let our advanced AI automatically
            detect, track, and extract license plate numbers with precision.
          </p>
        </div>

        {/* Upload Card */}
        <div className="bg-slate-900/30 border border-slate-800/50 rounded-2xl p-8 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-6">
            <h2 className="text-lg font-semibold text-white">Upload Video</h2>
            <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-400">
              Step 1
            </span>
          </div>

          <label
            htmlFor="video-upload"
            className={`relative flex flex-col items-center justify-center w-full h-52 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 group overflow-hidden ${
              videoFile
                ? "border-cyan-500/50 bg-cyan-500/5"
                : "border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/20"
            }`}
          >
            {videoFile ? (
              <div className="flex flex-col items-center gap-4">
                <FileVideo className="w-10 h-10 text-cyan-400" />
                <p className="text-white font-semibold">{videoFile.name}</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <Upload className="w-10 h-10 text-slate-500 group-hover:text-cyan-400" />
                <p className="text-white font-semibold">
                  Drop your video here or{" "}
                  <span className="text-cyan-400">browse</span>
                </p>
              </div>
            )}

            <input
              id="video-upload"
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          <button
            onClick={handleUpload}
            disabled={uploading || !videoFile}
            className="relative w-full mt-6 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold px-6 py-4 rounded-xl"
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing Video...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Scan className="w-5 h-5" />
                Analyze Video
              </span>
            )}
          </button>
        </div>

        {/* Results */}
        {detectedCars.length > 0 && (
          <div className="mt-8 bg-slate-900/30 border border-slate-800/50 rounded-2xl p-8">
            <h2 className="text-lg font-semibold text-white mb-4">
              Detection Complete
            </h2>

            <div className="space-y-3">
              {detectedCars.map((car, i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 bg-slate-800/30 border border-slate-700/50 rounded-xl px-5 py-4"
                >
                  <span className="text-white text-lg font-mono">
                    Car {car.car_id}: {car.plate}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Download Button */}
        {downloadUrl && (
          <a
            href={downloadUrl}
            target="_blank"
            className="flex items-center justify-center gap-2 w-full mt-6 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold px-6 py-4 rounded-xl"
          >
            <Download className="w-5 h-5" />
            Download Processed Video
          </a>
        )}
      </main>
    </div>
  );
}
