import Image from "next/image";
import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-meteora-border/60 bg-meteora-bg">
      <div className="px-5 sm:px-8">
        <div className="mx-auto grid max-w-meteora grid-cols-1 items-center justify-items-center gap-3 py-3 md:min-h-24 md:grid-cols-[1fr_auto_1fr] md:py-2">
          <Link
            href="/"
            aria-label="Meteora — página inicial"
            className="rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-meteora-accent md:justify-self-start"
          >
            <Image
              src="/images/logo_meteora_sem_fundo.png"
              alt="Meteora"
              width={80}
              height={80}
              priority
              className="size-20 object-contain"
            />
          </Link>

          <nav
            aria-label="Navegação principal"
            className="flex items-center gap-8 text-sm text-meteora-muted md:gap-12"
          >
            <a
              href="#agora"
              className="rounded-sm transition-colors hover:text-meteora-text focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-meteora-accent"
            >
              Agora
            </a>

            <a
              href="#previsao"
              className="rounded-sm transition-colors hover:text-meteora-text focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-meteora-accent"
            >
              Previsão
            </a>

            <a
              href="#estacao"
              className="rounded-sm transition-colors hover:text-meteora-text focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-meteora-accent"
            >
              Nossa estação
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
