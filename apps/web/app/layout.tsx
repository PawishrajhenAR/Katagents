import type { Metadata } from "next";
import { Providers } from "@/providers/providers";
import "./globals.css";
import "../styles/google-sans-flex.css";

export const metadata: Metadata = {
  title: "KatalyzU — Agent Automation",
  description: "Run AI agents for email outreach — research, draft, approve, send.",
  icons: {
    icon: "/KatalyzU.svg",
    apple: "/KatalyzU.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
