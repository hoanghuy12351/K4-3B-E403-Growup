"use client";
import { Spin } from "antd";
export default function Loading() {
  return <div className="loading-state" role="status" aria-label="Đang tải"><Spin size="large" /><p>Đang tải…</p></div>;
}

