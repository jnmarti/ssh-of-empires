import { ScrollReveal } from "@/components/effects/scroll-reveal";

export function Civilizations() {
  return (
    <section
      className="py-24 bg-[#0a0a0a] relative overflow-hidden"
      id="field-guide"
    >
      <div className="container mx-auto px-6">
        <ScrollReveal>
          <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8">
            <div className="max-w-xl">
              <h2 className="text-xs font-label uppercase tracking-[0.4em] text-tertiary mb-4">
                &gt; [ FIELD GUIDE ]
              </h2>
              <h3 className="text-4xl md:text-5xl font-headline font-bold uppercase leading-tight">
                Read The Battlefield
              </h3>
            </div>
            <div className="text-on-surface-variant font-body text-sm uppercase tracking-widest pb-2">
              Current prototype symbols from the game map
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
                Resources
              </h5>
              <ul className="font-body text-xs text-on-surface-variant space-y-3 uppercase tracking-wider">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  木 Tree: wood
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  果 Berry Bush: food
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  鹿 Gazelle / 肉 Carcass: hunt food
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-primary shrink-0" />
                  金 Gold Vein / 石 Stone Outcrop
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
                Units
              </h5>
              <ul className="font-body text-xs text-on-surface-variant space-y-3 uppercase tracking-wider">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-outline-variant shrink-0" />
                  民 Villager: gather, build, hunt
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-outline-variant shrink-0" />
                  馬 Scout: vision and early pressure
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-outline-variant shrink-0" />
                  兵 / 斧 / 剣: barracks infantry line
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
                Buildings
              </h5>
              <ul className="font-body text-xs text-on-surface-variant space-y-3 uppercase tracking-wider">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-secondary shrink-0" />
                  町 Town Center: villagers and age-up
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-secondary shrink-0" />
                  家 House: population cap
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-secondary shrink-0" />
                  粉 Mill / 伐 Lumber Camp / 陣 Barracks
                </li>
              </ul>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
