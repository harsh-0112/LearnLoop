export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-24">
      <h1 className="text-4xl font-bold">LearnLoop</h1>
      <p className="text-lg text-gray-500">Adaptive AI education platform</p>
      <p className="text-sm text-gray-400">
        API: {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
      </p>
    </main>
  );
}
