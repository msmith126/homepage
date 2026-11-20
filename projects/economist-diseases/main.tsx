import { createRoot } from "react-dom/client";
import { Barplot } from "./Barplot";

// Placeholder values: swap in the real data from the Economist chart
const data = [
  { name: "Disease A", value: 40 },
  { name: "Disease B", value: 25 },
  { name: "Disease C", value: 12 },
];

createRoot(document.getElementById("root")!).render(
  <Barplot width={700} height={400} data={data} />,
);
