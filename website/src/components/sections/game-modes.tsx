import { ScrollReveal } from "@/components/effects/scroll-reveal";
import { MULTIPLAYER_GUIDE_URL, README_URL } from "@/lib/site";

export function GameModes() {
  return (
    <section className="py-24 bg-surface" id="modes">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-[1px]">
          <ScrollReveal direction="left">
            <div className="group relative bg-surface-container-high p-12 overflow-hidden h-full">
              <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span
                className="material-symbols-outlined text-6xl text-primary mb-8 block"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                person
              </span>
              <h4 className="text-3xl font-headline font-bold mb-6 uppercase">
                Single Player
              </h4>
              <p className="text-on-surface-variant font-body mb-8 leading-relaxed">
                Start with one Town Center, three villagers, and one scout, then
                build up your economy and eliminate the AI civilization. The core
                opening is familiar RTS work: scout early, avoid population caps,
                and transition from economy into barracks pressure.
              </p>
              <a
                className="inline-flex items-center text-primary font-label text-xs font-bold uppercase tracking-widest gap-2"
                href={README_URL}
                target="_blank"
                rel="noreferrer"
              >
                &gt; OPEN README
              </a>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="right" delay={150}>
            <div className="group relative bg-surface-container-high p-12 overflow-hidden border-l border-outline-variant/10 h-full">
              <div className="absolute inset-0 bg-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span
                className="material-symbols-outlined text-6xl text-secondary mb-8 block"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                groups
              </span>
              <h4 className="text-3xl font-headline font-bold mb-6 uppercase">
                Multiplayer Rooms
              </h4>
              <p className="text-on-surface-variant font-body mb-8 leading-relaxed">
                Create or join a private room, share the room code, wait until
                every player is ready, and let the host start the match. The
                current prototype supports two to three players in one shared,
                authoritative simulation, whether those players are humans, coding
                agents, or a mix of both.
              </p>
              <a
                className="inline-flex items-center text-secondary font-label text-xs font-bold uppercase tracking-widest gap-2"
                href={MULTIPLAYER_GUIDE_URL}
                target="_blank"
                rel="noreferrer"
              >
                &gt; READ MULTIPLAYER MANUAL
              </a>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
