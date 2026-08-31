import { useLayoutEffect, useRef, useState, useCallback } from 'react';
import RoadmapNode from './RoadmapNode';
import './Roadmap.css';

/**
 * Groups nodes by `stage` into columns, then draws an SVG connector for
 * every prerequisite edge by measuring each node's live position. This is
 * the "transit map" signature visualization reused (in compact form) on
 * the landing page, and (full form) on the Skill Analysis and Roadmap pages.
 */
export default function Roadmap({ nodes, onSelectNode, compact = false }) {
  const containerRef = useRef(null);
  const nodeRefs = useRef({});
  const [paths, setPaths] = useState([]);
  const [size, setSize] = useState({ width: 0, height: 0 });

  const stages = [...new Set(nodes.map((n) => n.stage))].sort((a, b) => a - b);
  const columns = stages.map((stage) => nodes.filter((n) => n.stage === stage));

  const recomputePaths = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    const newPaths = [];

    nodes.forEach((node) => {
      (node.prerequisites || []).forEach((prereqId) => {
        const fromEl = nodeRefs.current[prereqId];
        const toEl = nodeRefs.current[node.id];
        if (!fromEl || !toEl) return;
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();

        const x1 = fromRect.right - containerRect.left + container.scrollLeft;
        const y1 = fromRect.top + fromRect.height / 2 - containerRect.top + container.scrollTop;
        const x2 = toRect.left - containerRect.left + container.scrollLeft;
        const y2 = toRect.top + toRect.height / 2 - containerRect.top + container.scrollTop;
        const midX = (x1 + x2) / 2;

        newPaths.push({
          id: `${prereqId}-${node.id}`,
          d: `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`,
          dashed: node.status === 'locked',
          active: node.status === 'current' || node.status === 'adapted',
        });
      });
    });

    setPaths(newPaths);
    setSize({ width: container.scrollWidth, height: container.scrollHeight });
  }, [nodes]);

  useLayoutEffect(() => {
    recomputePaths();
    const handle = () => recomputePaths();
    window.addEventListener('resize', handle);
    const timeout = setTimeout(recomputePaths, 60); // catch font/layout settle
    return () => {
      window.removeEventListener('resize', handle);
      clearTimeout(timeout);
    };
  }, [recomputePaths]);

  return (
    <div className={`roadmap ${compact ? 'roadmap-compact' : ''}`} ref={containerRef}>
      <svg className="roadmap-svg" width={size.width} height={size.height} aria-hidden="true">
        {paths.map((p) => (
          <path
            key={p.id}
            d={p.d}
            fill="none"
            stroke={p.active ? 'var(--amber)' : 'var(--line-strong)'}
            strokeWidth={p.active ? 2.5 : 2}
            strokeDasharray={p.dashed ? '5 5' : undefined}
          />
        ))}
      </svg>
      <div className="roadmap-columns">
        {columns.map((col, i) => (
          <div className="roadmap-column" key={stages[i]}>
            {col.map((node) => (
              <RoadmapNode
                key={node.id}
                node={node}
                compact={compact}
                onSelect={onSelectNode}
                ref={(el) => {
                  nodeRefs.current[node.id] = el;
                }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}