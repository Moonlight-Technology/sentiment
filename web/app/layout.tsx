import type { Metadata } from "next";
import "./global.css";
import { AppProviders } from "@/components/providers";

export const metadata: Metadata = {
  title: "Sentiment Dashboard",
  description: "Monitor sentiment signals across channels",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <AppProviders>
          {children}
        </AppProviders>
      </body>
    </html>
  );
}
