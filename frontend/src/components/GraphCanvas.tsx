'use client';

import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { GraphData } from '@/types';
import { Network, Maximize2 } from 'lucide-react';

interface GraphCanvasProps {
  graphData?: GraphData | null;
  onSelectEntity?: (entityName: string) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  COMPANY: '#2C4C3B',
  METRIC: '#059669',
  CURRENCY: '#D97706',
  PERCENTAGE: '#7C3AED',
  TIMEFRAME: '#2563EB',
  CONCEPT: '#78716C',
};

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  graphData,
  onSelectEntity,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: cytoscape.ElementDefinition[] = [];

    // Add nodes
    if (graphData?.nodes) {
      graphData.nodes.forEach((node) => {
        elements.push({
          group: 'nodes',
          data: {
            id: node.id,
            label: node.label,
            category: node.category,
            color: CATEGORY_COLORS[node.category] || CATEGORY_COLORS.CONCEPT,
          },
        });
      });
    }

    // Add edges
    if (graphData?.edges) {
      graphData.edges.forEach((edge) => {
        elements.push({
          group: 'edges',
          data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.label,
            evidence: edge.evidence,
          },
        });
      });
    }

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            label: 'data(label)',
            color: '#292524',
            'font-size': '11px',
            'font-family': 'Figtree, sans-serif',
            'font-weight': 'bold',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            width: 26,
            height: 26,
            'border-width': 2,
            'border-color': '#FFFFFF',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#2C4C3B',
            width: 32,
            height: 32,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': '#D6CEBE',
            'target-arrow-color': '#8FA998',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': '9px',
            color: '#78716C',
            'text-rotation': 'autorotate',
            'text-background-color': '#FDFBF7',
            'text-background-opacity': 0.9,
            'text-background-padding': '3px',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 30,
        nodeRepulsion: () => 4500,
        idealEdgeLength: () => 90,
      },
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode(node.data());
      if (onSelectEntity) {
        onSelectEntity(node.data('label'));
      }
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData, onSelectEntity]);

  const handleFit = () => {
    cyRef.current?.fit();
  };

  return (
    <div className="h-full flex flex-col bg-[#FDFBF7] relative select-none">
      {/* Top Header / Legend */}
      <div className="h-11 border-b border-[#E7E2D9] px-3.5 flex items-center justify-between text-xs bg-white shadow-warm">
        <div className="flex items-center space-x-2">
          <Network className="w-4 h-4 text-[#2C4C3B]" />
          <span className="text-xs font-serif font-bold text-[#292524]">
            KùzuDB Property Subgraph
          </span>
          <span className="text-[11px] text-[#78716C] font-mono">
            ({graphData?.nodes?.length || 0} entities, {graphData?.edges?.length || 0} links)
          </span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={handleFit}
            className="p-1 hover:bg-[#E4EDE6] rounded-lg text-[#78716C] hover:text-[#292524] transition-colors"
            title="Fit to view"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Category Legend Bar */}
      <div className="px-3.5 py-2 border-b border-[#E7E2D9] bg-[#FDFBF7] flex items-center space-x-3 text-[11px] text-[#78716C] overflow-x-auto">
        <span className="font-serif text-[10px] font-bold text-[#292524] uppercase tracking-wider">
          Legend:
        </span>
        {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
          <div key={cat} className="flex items-center space-x-1.5 flex-shrink-0">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span className="font-medium text-[10px]">{cat}</span>
          </div>
        ))}
      </div>

      {/* Cytoscape Canvas */}
      <div className="flex-1 w-full h-full relative">
        <div ref={containerRef} className="w-full h-full" />

        {(!graphData?.nodes || graphData.nodes.length === 0) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center text-[#78716C] pointer-events-none">
            <Network className="w-12 h-12 mb-3 opacity-30 text-[#2C4C3B]" />
            <p className="font-serif font-semibold text-sm text-[#292524]">No Subgraph Active</p>
            <p className="text-xs text-[#78716C] max-w-xs mt-1 leading-relaxed">
              Ask a question involving entities, companies, or financial metrics to traverse and visualize the
              KùzuDB property graph.
            </p>
          </div>
        )}

        {/* Selected Entity Card */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 right-4 p-3.5 rounded-2xl bg-white/95 border border-[#E7E2D9] backdrop-blur-md text-xs shadow-warm animate-in fade-in">
            <div className="flex items-center justify-between">
              <span className="font-serif font-bold text-sm text-[#292524]">{selectedNode.label}</span>
              <span
                className="px-2 py-0.5 rounded-full text-[10px] font-medium text-white shadow-warm"
                style={{
                  backgroundColor:
                    CATEGORY_COLORS[selectedNode.category] || CATEGORY_COLORS.CONCEPT,
                }}
              >
                {selectedNode.category}
              </span>
            </div>
            <p className="text-[11px] text-[#78716C] mt-1">
              Connected entity node in KùzuDB graph database. Click adjacent nodes to traverse relations.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
