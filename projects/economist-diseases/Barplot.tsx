import { max, scaleBand, scaleLinear } from "d3";

type Datum = { count: number; name: string };

type BarplotProps = {
  width: number;
  height: number;
  data: Datum[];
};

export const Barplot = ({ width, height, data }: BarplotProps) => {
  const boundsWidth = width;
  const boundsHeight = height;

  const sorted = [...data].sort((a, b) => b.count - a.count);
  const yScale = scaleBand()
    .domain(sorted.map((d) => d.name))
    .range([0, boundsHeight])
    .padding(0.2);

  const xScale = scaleLinear()
    .domain([0, max(data, (d) => d.count) ?? 0])
    .range([0, boundsWidth]);

  const allRects = sorted.map((d) => {
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
          x={d.count > 7 ? 2 : xScale(d.count) + 2}
          y={y + yScale.bandwidth() / 2}
          textAnchor="start"
          dominantBaseline="middle"
          fontSize={14}
          fill={d.count > 7 ? "white" : "black"}
        >
          {d.name}
        </text>
      </g>
    );
  });

  const grid = xScale
    .ticks(10)
    .slice(1)
    .map((count, i) => (
      <g key={i}>
        <line
          x1={xScale(count)}
          x2={xScale(count)}
          y1={0}
          y2={boundsHeight}
          stroke="#808080"
          opacity={0.2}
        />
        <text
          x={xScale(count)}
          y={-10}
          textAnchor="middle"
          alignmentBaseline="central"
          fontSize={12}
          fill="#808080"
          opacity={1}
        >
          {count}
        </text>
      </g>
    ));
  return (
    <div>
      <svg width={width} height={height} style={{ overflow: "visible" }}>
        <g>
          {grid}
          {allRects}
          <g>
            <line
              x1={xScale(0)}
              x2={xScale(0)}
              y1={0}
              y2={boundsHeight}
              stroke="black"
              opacity={0.8}
            />
            <text
              x={xScale(0)}
              y={-10}
              textAnchor="middle"
              alignmentBaseline="central"
              fontSize={12}
              fill="#070606"
              opacity={1}
            >
              {0}
            </text>
          </g>
        </g>
      </svg>
    </div>
  );
};
