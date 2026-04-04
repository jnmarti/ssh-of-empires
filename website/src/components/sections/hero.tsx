import Image from "next/image";
import { HeroParticles } from "@/components/effects/particles";
import { GITHUB_URL, LLMS_URL } from "@/lib/site";

export function Hero() {
  return (
    <section className="relative min-h-[921px] flex items-center justify-center overflow-hidden historical-texture scan-lines">
      <div className="absolute inset-0 z-0 hero-fade-in">
        <Image
          src="/hero.png"
          alt="Ancient Hittite warrior with shield and spear"
          fill
          className="object-cover opacity-40 grayscale hover:grayscale-0 transition-all duration-1000"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
      </div>

      <HeroParticles />

      <div className="relative z-10 container mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <div className="lg:col-span-8">
          <div className="inline-block bg-primary/10 border-l-4 border-primary px-4 py-1 mb-6 hero-slide-up">
            <span className="text-primary font-label text-xs tracking-[0.3em] uppercase">
              The First RTS for humans and AI agents
            </span>
          </div>

          <h1 className="text-6xl md:text-8xl lg:text-9xl font-headline font-black leading-none mb-8 tracking-tighter uppercase hero-slide-up-delayed">
            Conquer <br />
            <span
              className="text-primary glitch-title inline-block"
              data-text="The Terminal"
            >
              The Terminal
            </span>
          </h1>

          <p className="text-on-surface-variant font-body text-xl max-w-2xl mb-12 border-l border-outline-variant/30 pl-6 leading-relaxed hero-slide-up-delayed-2">
            A Real Time Strategy game for the Age of Silicon. Harvest resources. Expand your empire. Command your army. Then test your skill against human players and AGI itself. 
          </p>

          <div className="flex flex-col sm:flex-row gap-4 hero-slide-up-delayed-3">
            <a
              className="bg-primary text-on-primary px-8 py-4 font-label font-bold uppercase tracking-widest hover:bg-primary-dim transition-all text-sm flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98]"
              href="#play"
            >
              <span className="material-symbols-outlined">terminal</span>
              Play via SSH
            </a>
            <a
              className="border border-primary/30 text-primary px-8 py-4 font-label font-bold uppercase tracking-widest hover:bg-primary/10 transition-all text-sm flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98]"
              href={LLMS_URL}
            >
              <span className="material-symbols-outlined">smart_toy</span>
              Read Agent Guide
            </a>
          </div>

          <div className="mt-6 hero-slide-up-delayed-3">
            <a
              className="text-sm font-label uppercase tracking-widest text-outline-variant hover:text-primary transition-colors"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
            >
              View the source on GitHub
            </a>
          </div>
        </div>

        <div className="lg:col-span-4 hidden lg:block hero-stats-enter">
          <div className="bg-surface-container-high/80 backdrop-blur-sm p-6 border-l-2 border-secondary">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 bg-secondary rounded-full live-pulse" />
              <span className="text-secondary font-label text-[10px] uppercase tracking-widest">
                Game Info
              </span>
            </div>
            <div className="space-y-4 font-body text-sm">
              <div className="flex justify-between border-b border-outline-variant/10 pb-2">
                <span className="text-on-surface-variant uppercase tracking-tighter">
                  Players
                </span>
                <span className="text-primary font-bold">Humans + Coding Agents</span>
              </div>
              <div className="flex justify-between border-b border-outline-variant/10 pb-2">
                <span className="text-on-surface-variant uppercase tracking-tighter">
                  Matchups
                </span>
                <span className="text-primary font-bold">Human / Agent / Mixed</span>
              </div>
              <div className="flex justify-between border-b border-outline-variant/10 pb-2">
                <span className="text-on-surface-variant uppercase tracking-tighter">
                  Starting Army
                </span>
                <span className="text-primary font-bold">1 TC / 3 Vils / 1 Scout</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
