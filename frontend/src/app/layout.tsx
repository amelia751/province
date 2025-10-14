import type { Metadata } from "next";
import localFont from "next/font/local";
import { ClerkProvider } from '@clerk/nextjs';
import "./globals.css";

const fkGrotesk = localFont({
  src: [
    {
      path: "../../public/fonts/FKGrotesk-Regular.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../../public/fonts/FKGrotesk-Medium.woff2",
      weight: "500",
      style: "normal",
    },
    {
      path: "../../public/fonts/FKGrotesk-SemiBold.woff2",
      weight: "600",
      style: "normal",
    },
    {
      path: "../../public/fonts/FKGrotesk-Bold.woff2",
      weight: "700",
      style: "normal",
    },
  ],
  variable: "--font-fk-grotesk",
  fallback: ["system-ui", "arial"],
});

export const metadata: Metadata = {
  title: "Province",
  description: "Legal case intelligence platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      afterSignInUrl="/app"
      afterSignUpUrl="/app"
    >
      <html lang="en">
        <body className={fkGrotesk.variable}>{children}</body>
      </html>
    </ClerkProvider>
  );
}
