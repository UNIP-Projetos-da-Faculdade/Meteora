import Header from "@/components/ui/Header";
import Dashboard from "@/components/Dashboard";

export default function Home() {
  return (
    <>
      <Header />

      <main id="conteudo" className="flex-1 px-4 py-7 sm:px-8 sm:py-8">
        <div className="mx-auto max-w-meteora">
          <Dashboard />
        </div>
      </main>
      <footer className="px-4 pb-7 sm:px-8">
        <div className="mx-auto flex max-w-meteora flex-wrap justify-between gap-3 text-[10px] leading-relaxed text-meteora-muted">
          <p>Meteora · Dados da estação ESP32</p>
          <p>São José do Rio Preto, SP · Horário de Brasília</p>
        </div>
      </footer>
    </>
  );
}
