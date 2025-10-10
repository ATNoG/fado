"use client";

import React, { useState } from "react";

export default function YamlUploader() {
  const [status, setStatus] = useState("");
  const [fileName, setFileName] = useState("");
  const [fileContent, setFileContent] = useState("");

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      setStatus("❌ No file selected.");
      setFileName("");
      return;
    }

    setFileName(file.name);
    setStatus("⏳ Uploading...");

    const formData = new FormData();
    formData.append("upload", file);

    try {
      const response = await fetch("http://localhost:8000/yaml_upload/test@exploit.com", {
        method: "POST",
        body: formData,
      });

      const result = await response.text(); // always read as text
      if (!response.ok) throw new Error(result);

      setStatus("✅ Upload successful");
      setFileContent(result);
    } catch (error) {
      setStatus(`❌ Error: ${error.message}`);
      setFileContent("");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <div className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-xl space-y-4">
        <h1 className="text-2xl font-semibold text-gray-800">File Uploader</h1>

        <input
          type="file"
          accept=".yaml,.yml"
          onChange={handleUpload}
          className="block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {fileName && (
          <p className="text-sm text-gray-600">
            📄 <span className="font-medium">Selected:</span> {fileName}
          </p>
        )}

        {status && (
          <p
            className={`text-sm ${
              status.startsWith("✅")
                ? "text-green-600"
                : status.startsWith("⏳")
                ? "text-yellow-600"
                : "text-red-600"
            }`}
          >
            {status}
          </p>
        )}

        {fileContent && (
          <div className="bg-gray-100 text-gray-800 border border-gray-300 rounded-lg p-4 max-h-96 overflow-auto font-mono text-sm whitespace-pre-wrap">
            {fileContent}
          </div>
        )}
      </div>
    </div>
  );
}
