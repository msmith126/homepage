import { createRoot } from "react-dom/client";
import { Barplot } from "./Barplot";
import { data } from "./data";

createRoot(document.getElementById("root")!).render(
  <Barplot width={700} height={400} data={data} />,
);
