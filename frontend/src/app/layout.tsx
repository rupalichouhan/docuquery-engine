import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DocuQuery Engine — Warm Research Library',
  description: 'Self-Corrective Hybrid Graph-RAG & Numerical Verification Document Intelligence',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full font-sans antialiased bg-[#FDFBF7] text-[#292524] selection:bg-[#D1FAE5] selection:text-[#065F46]">
        {children}
      </body>
    </html>
  );
}
