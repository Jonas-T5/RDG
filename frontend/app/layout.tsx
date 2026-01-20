// app/layout.tsx
import '../styles/globals.css';

export const metadata = {
    title: 'Darwin Gödel Machine',
    description: 'Self-improving AI Agent System with Ralph Loop',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
