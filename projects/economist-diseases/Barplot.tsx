import { max, scaleBand, scaleLinear } from "d3";

type Datum = { count: number; name: string };

type BarplotProps = {
  width: number;
  height: number;
  data: Datum[];
};

const MARGIN = { top: 20, right: 20, bottom: 20, left: 120 };

export const Barplot = ({ width, height, data }: BarplotProps) => {
  const boundsWidth = width - MARGIN.left - MARGIN.right;
  const boundsHeight = height - MARGIN.top - MARGIN.bottom;

  const yScale = scaleBand()
    .domain(data.map((d) => d.name))
    .range([0, boundsHeight])
    .padding(0.2);

  const xScale = scaleLinear()
    .domain([0, max(data, (d) => d.count) ?? 0])
    .range([0, boundsWidth]);

  return (
    <svg width={width} height={height}>
      <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
        {data.map((d) => {
          const y = yScale(d.name) ?? 0;
          return (
            <g key={d.name}>
              <rect
                x={0}
                y={y}
                width={xScale(d.count)}
                height={yScale.bandwidth()}
                fill="#006ba2"
              />
              <text
                x={-8}
                y={y + yScale.bandwidth() / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize={12}
              >
                {d.name}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
};
