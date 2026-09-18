import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import Providers from "./providers";
import "antd/dist/reset.css";
import "@/styles/globals.css";

const nunito = Nunito({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-nunito",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Growup · Không gian giảng viên",
  description: "Khung giao diện cho tính năng kiểm tra mức hiểu trên VLearn.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" className={nunito.variable}>
      <body className={nunito.className}>
        <AntdRegistry><Providers>{children}</Providers></AntdRegistry>
      </body>
    </html>
  );
}

