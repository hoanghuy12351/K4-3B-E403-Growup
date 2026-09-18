import type { Metadata } from "next";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import Providers from "./providers";
import "antd/dist/reset.css";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Growup · Không gian giảng viên",
  description: "Khung giao diện cho tính năng kiểm tra mức hiểu trên VLearn.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body>
    <AntdRegistry><Providers>{children}</Providers></AntdRegistry>
  </body></html>;
}

