import type { NextConfig } from "next";

const config: NextConfig = {
  allowedDevOrigins: ["127.0.0.1:3000", "localhost:3000", "127.0.0.1", "localhost"],
};

export default config;

