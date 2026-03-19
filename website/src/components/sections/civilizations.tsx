import { ScrollReveal } from "@/components/effects/scroll-reveal";

export function Civilizations() {
  return (
    <section className="py-24 bg-[#0a0a0a] relative overflow-hidden">
      <div className="container mx-auto px-6">
        <ScrollReveal>
          <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8">
            <div className="max-w-xl">
              <h2 className="text-xs font-label uppercase tracking-[0.4em] text-tertiary mb-4">
                &gt; [ DATABASE: FACTIONS ]
              </h2>
              <h3 className="text-4xl md:text-5xl font-headline font-bold uppercase leading-tight">
                Pick Your Dynasty
              </h3>
            </div>
            <div className="text-on-surface-variant font-body text-sm uppercase tracking-widest pb-2">
              Total Records: 12 Ancient Powers
            </div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ScrollReveal delay={0}>
            <div className="bg-surface-container-low border-b-4 border-primary p-8 h-full">
              <div className="flex justify-between items-start mb-12">
                <span className="text-4xl font-headline text-primary opacity-50">
                  01.
                </span>
                <span className="material-symbols-outlined text-primary">
                  landscape
                </span>
              </div>
              <h5 className="text-2xl font-headline font-bold mb-4 uppercase">
                Egyptians
              </h5>
              <ul className="font-body text-xs text-on-surface-variant space-y-3 uppercase tracking-wider">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  Build Speed: +25%
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  Gold Mining: +15%
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  Special: Chariot Archers
                </li>
              </ul>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={150}>
            <div className="bg-surface-container-low border-b-4 border-outline-variant p-8 h-full">
              <div className="flex justify-between items-start mb-12">
                <span className="text-4xl font-headline text-outline-variant opacity-50">
                  02.
                </span>
                <span className="material-symbols-outlined text-outline-variant">
                  swords
                </span>
              </div>
              <h5 className="text-2xl font-headline font-bold mb-4 uppercase">
                Hittites
              </h5>
              <ul className="font-body text-xs text-on-surface-variant space-y-3 uppercase tracking-wider">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-outline-variant shrink-0" />
                  Siege HP: +50%
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-outline-variant shrink-0" />
                  Archery Range: +1
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-outline-variant shrink-0" />
                  Special: War Chariots
                </li>
              </ul>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={300}>
            <div className="bg-surface-container-low border-b-4 border-secondary p-8 h-full">
              <div className="flex justify-between items-start mb-12">
                <span className="text-4xl font-headline text-secondary opacity-50">
                  03.
                </span>
                <span className="material-symbols-outlined text-secondary">
                  account_balance
                </span>
              </div>
              <h5 className="text-2xl font-headline font-bold mb-4 uppercase">
                Greeks
              </h5>
              <ul className="font-body text-xs text-on-surface-variant space-y-3 uppercase tracking-wider">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-secondary shrink-0" />
                  Academy Tech: -30%
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-secondary shrink-0" />
                  Infantry Speed: +10%
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-secondary shrink-0" />
                  Special: Hoplites
                </li>
              </ul>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
