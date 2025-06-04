import { useState, useMemo, useEffect, useRef } from "react";
import { scaleOrdinal } from "d3-scale";
import { schemeDark2 } from "d3-scale-chromatic";

import cloud from "d3-cloud";
import seedrandom from "seedrandom";

const colorScale = scaleOrdinal(schemeDark2.slice(0, 6));

export default function WordCloud({ w, filters, clc }) {
  const containerRef = useRef(null);
  const [layoutWords, setLayoutWords] = useState([]);
  const [dimensions, setDimensions] = useState({ width: 1000, height: 200 });

  const wordsKey = useMemo(() => JSON.stringify(w), [w]);

  const total = useMemo(() => {
    return w.map((one) => one.value).reduce((ps, a) => ps + a, 0.00001);
  }, [w]);

  const words = useMemo(() => {
    return w.map((one) => ({
      text: one.text,
      value: Math.min(40, Math.round((one.value * 1000) / total)),
    }));
  }, [w, total]);

  useEffect(() => {
    if (!words || words.length === 0 || !dimensions.width) return;

    const rng = seedrandom("fixed-seed");

    const layout = cloud()
      .size([dimensions.width, dimensions.height])
      .words(words.map((w) => ({ ...w })))
      .padding(2)
      .rotate(() => 0)
      .font("Poppins")
      .fontSize((d) => d.value)
      .random(rng)
      .on("end", (output) => {
        setLayoutWords(output);
      });

    layout.start();
  }, [wordsKey, dimensions]);

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width } = entry.contentRect;
        setDimensions({
          width,
          height: 200, // Можно сделать пропорциональной, если нужно
        });
      }
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      {layoutWords.length === 0 ? (
        <div style={{ height: dimensions.height }}>Loading cloud...</div>
      ) : (
        <svg
          width="100%"
          height={dimensions.height}
          viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
        >
          <g
            transform={`translate(${dimensions.width / 2},${
              dimensions.height / 2
            })`}
          >
            {layoutWords.map((word, i) => (
              <text
                key={word.text}
                fontFamily="Poppins"
                fontSize={word.size}
                fill={
                  filters.length === 0 || filters.includes(word.text)
                    ? colorScale(i)
                    : "#888"
                }
                textAnchor="middle"
                transform={`translate(${word.x},${word.y}) rotate(${word.rotate})`}
                style={{ cursor: "pointer" }}
                onClick={() => clc(word.text)}
              >
                {word.text}
              </text>
            ))}
          </g>
        </svg>
      )}
    </div>
  );
}
