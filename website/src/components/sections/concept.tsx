import { ScrollReveal } from "@/components/effects/scroll-reveal";
import { BattlefieldPreview } from "@/components/ui/battlefield-preview";

export function Concept() {
  return (
    <section className="py-24 bg-surface" id="game">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div>
            <ScrollReveal>
              <h2 className="text-xs font-label uppercase tracking-[0.4em] text-primary-container mb-4">
                &gt; [ GAMEPLAY ]
              </h2>
              <h3 className="text-4xl md:text-5xl font-headline font-bold mb-8 uppercase leading-tight">
                A Real RTS <br />
                With Terminal Controls
              </h3>
            </ScrollReveal>
            <ScrollReveal delay={150}>
              <div className="space-y-6 text-on-surface-variant font-body text-lg leading-relaxed">
                <p>
                  SSH of Empires keeps the classic RTS loop intact: scout the map,
                  gather resources, build houses before you get population capped,
                  place drop-off buildings efficiently, and pressure the enemy
                  before they outscale you.
                </p>
                <p>
                  The interface is compact and direct, keeping the focus on{" "}
                  <span className="text-on-surface font-bold">
                    economy, scouting, timing, and battles
                  </span>{" "}
                  instead of menus and overhead.
                </p>
                <p>
                  It still feels like a real Age-inspired RTS: expand your base,
                  move through the ages, and pressure the enemy before they
                  outscale you.
                </p>
              </div>
            </ScrollReveal>
            <ScrollReveal delay={300}>
              <div className="mt-12 grid grid-cols-2 gap-8">
                <div className="border-t border-outline-variant/20 pt-4">
                  <span className="text-3xl font-headline text-primary block mb-2">
                    Stone / Tool / Bronze
                  </span>
                  <span className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant leading-none">
                    Age Progression
                  </span>
                </div>
                <div className="border-t border-outline-variant/20 pt-4">
                  <span className="text-3xl font-headline text-primary block mb-2">
                    Human + Agent Play
                  </span>
                  <span className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant leading-none">
                    Shared Live Interface
                  </span>
                </div>
              </div>
            </ScrollReveal>
          </div>

          <ScrollReveal direction="right" delay={200}>
            <BattlefieldPreview />
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
