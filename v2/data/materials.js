/* Material take-off data.
   Recipe is PER 47mm brick. Each 215x65x47 brick is sliced (losing a 3mm kerf)
   into TWO 22mm slips, so: bricks_to_make = equivalent-whole-slips / 2, and
   material = bricks_to_make x recipe. Equivalent-whole-slip = whole + half/2
   (two half-bricks <=107.5x65 count as one). B2 is supplied by Wuhan -> shown
   for quantities but no material calc. Red = B2 + R-Y101-3 + D1; Black = B-3. */
window.DATA_materials = {
  brick_mm: 47, slip_mm: 22, kerf_mm: 3, surplus: 0.15,
  mats: ["Sand", "Lime", "Additives", "O", "RY101", "B"],
  rows: [
    { id: "B2",       colour: "red",   pct: 10,  whole: 564,  half: 32,  equiv: 580,    wuhan: true },
    { id: "R-Y101-3", colour: "red",   pct: 40,  whole: 2258, half: 128, equiv: 2322,
      recipe: { Sand: 1.009556, Lime: 0.135193, Additives: 0.201382, RY101: 0.036637 } },
    { id: "D1",       colour: "red",   pct: 50,  whole: 2822, half: 160, equiv: 2902,
      recipe: { Sand: 1.007271, Lime: 0.134887, Additives: 0.200927, O: 0.029064, RY101: 0.009766, B: 0.000488 } },
    { id: "B-3",      colour: "black", pct: 100, whole: 1230, half: 503, equiv: 1481.5,
      recipe: { Sand: 1.009556, Lime: 0.135193, Additives: 0.201382, B: 0.036637 } }
  ]
};
