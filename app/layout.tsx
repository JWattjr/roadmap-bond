import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Roadmap Bond — Promises on the record",
  description: "Public roadmap promises backed by archived quotes, frozen criteria, immutable evidence, and finalized settlement on GenLayer StudioNet.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
