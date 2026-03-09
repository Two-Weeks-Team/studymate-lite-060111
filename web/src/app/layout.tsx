import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'StudyMate Lite',
  description: 'Instant flashcards from your notes – no accounts, no fees, just study.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 flex flex-col items-center p-4">
        {children}
      </body>
    </html>
  );
}
