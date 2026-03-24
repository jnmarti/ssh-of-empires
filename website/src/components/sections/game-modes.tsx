import { ScrollReveal } from "@/components/effects/scroll-reveal";

export function GameModes() {
  return (
    <section className="py-24 bg-surface">
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
                Campaign Mode
              </h4>
              <p className="text-on-surface-variant font-body mb-8 leading-relaxed">
                Relive the rise of the Hittite empire or the defense of the Greek
                city-states. Face off against advanced AI across 20+ historical
                campaigns programmed for tactical perfection.
              </p>
              <a
                className="inline-flex items-center text-primary font-label text-xs font-bold uppercase tracking-widest gap-2"
                href="#"
              >
                &gt; INITIALIZE_CHRONICLES
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
                Netwarfare
              </h4>
              <p className="text-on-surface-variant font-body mb-8 leading-relaxed">
                Challenge other terminal emperors in ranked 1v1 or 4v4 matches.
                Climb the global ladder and prove your shell-scripting dominance
                on the digital battlefield.
              </p>
              <a
                className="inline-flex items-center text-secondary font-label text-xs font-bold uppercase tracking-widest gap-2"
                href="#"
              >
                &gt; CONNECT_TO_LOBBY
              </a>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
