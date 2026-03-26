const battlefieldRows = [
  ", , , , . . t t t . . . . . . ,",
  ", , . . . b b . . . d . . . . ,",
  ", . BT BV BV BH . . BM . . . t . . ,",
  ", . t t BV . . BL . . BS . t t . ,",
  ". . t t . . BC . . . . g . d . .",
  ". . . . . BR BC . . . . . . . . .",
  ". . d . . . . . . , . . RT RV* RH .",
  ". . . . . . s . . . . RR RC RS . .",
  ". t t . . . CV . . . . CA CS . . .",
  ". t t . . . . . d . . . . . . .",
  ", . . . . . . . . . t t . . . ,",
  ", , . . . . . . . . . . . . , ,",
].map((row) => row.split(" "));

const sidebarLines = [
  "SSH of Empires",
  "",
  "Civ: Hittite",
  "Age: Tool Age",
  "Food: 145",
  "Wood: 120",
  "Gold: 35",
  "Stone: 0",
  "Pop: 9/12",
  "",
  "RedFox: Hittite",
  "CyanBot: Hittite",
  "",
  "Selected:",
  "You Clubman",
  "Tile: Red Villager",
];

const logLines = [
  "You: Barracks complete",
  "RedFox: Villager gathering berries",
  "CyanBot: Scout spotted near gold",
];

const ownerColors: Record<string, string> = {
  B: "#60a5fa",
  R: "#f87171",
  C: "#67e8f9",
};

const entityGlyphs: Record<string, string> = {
  T: "町",
  H: "家",
  L: "伐",
  M: "粉",
  R: "陣",
  V: "民",
  S: "馬",
  C: "兵",
  A: "斧",
  W: "剣",
};

const resourceGlyphs: Record<string, { glyph: string; color: string }> = {
  ".": { glyph: ".", color: "#6b7280" },
  ",": { glyph: ",", color: "#4b5563" },
  t: { glyph: "木", color: "#59ee50" },
  b: { glyph: "果", color: "#59ee50" },
  d: { glyph: "鹿", color: "#f5ce53" },
  g: { glyph: "金", color: "#f5ce53" },
  s: { glyph: "石", color: "#f3f4f6" },
};

function BattlefieldCell({ token }: { token: string }) {
  const selected = token.endsWith("*");
  const baseToken = selected ? token.slice(0, -1) : token;

  if (baseToken in resourceGlyphs) {
    const cell = resourceGlyphs[baseToken];
    return (
      <span
        className={`flex h-[18px] w-[18px] items-center justify-center text-[12px] leading-none ${
          selected ? "bg-primary/10 ring-1 ring-primary/40 rounded-[2px]" : ""
        }`}
        style={{ color: cell.color }}
      >
        {cell.glyph}
      </span>
    );
  }

  const owner = baseToken[0];
  const unitType = baseToken[1];
  const glyph = entityGlyphs[unitType] ?? ".";
  const color = ownerColors[owner] ?? "#ffffff";

  return (
    <span
      className={`flex h-[18px] w-[18px] items-center justify-center text-[12px] leading-none ${
        selected ? "bg-primary/10 ring-1 ring-primary/40 rounded-[2px]" : ""
      }`}
      style={{ color }}
    >
      {glyph}
    </span>
  );
}

export function BattlefieldPreview() {
  return (
    <div className="relative">
      <div className="bg-surface-container-lowest border border-outline-variant/20 p-2 shadow-2xl">
        <div className="bg-surface-container-low p-4 flex items-center justify-between border-b border-outline-variant/20">
          <div className="flex gap-2">
            <div className="w-2 h-2 bg-error rounded-full" />
            <div className="w-2 h-2 bg-tertiary rounded-full" />
            <div className="w-2 h-2 bg-secondary rounded-full" />
          </div>
          <span className="text-[10px] font-label text-on-surface-variant uppercase tracking-widest">
            LIVE_MATCH.TTY
          </span>
        </div>

        <div className="bg-black p-4 sm:p-5">
          <div className="grid gap-5 xl:grid-cols-[max-content_minmax(0,11rem)] items-start">
            <div className="overflow-x-auto">
              <div className="inline-flex flex-col border border-outline-variant/10 bg-black/70 p-2">
                {battlefieldRows.map((row, rowIndex) => (
                  <div key={rowIndex} className="flex">
                    {row.map((token, columnIndex) => (
                      <BattlefieldCell
                        key={`${rowIndex}-${columnIndex}`}
                        token={token}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>

            <div className="font-mono text-[10px] sm:text-[11px] leading-4 text-on-surface-variant">
              {sidebarLines.map((line, index) => (
                <div
                  key={`${line}-${index}`}
                  className={
                    index === 0 ? "font-bold text-on-surface" : undefined
                  }
                >
                  {line || "\u00A0"}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 border-t border-outline-variant/20 pt-3 font-mono text-[10px] sm:text-[11px] leading-4 text-on-surface-variant">
            {logLines.map((line) => (
              <div key={line}>
                <span className="text-primary mr-2">&gt;</span>
                {line}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
