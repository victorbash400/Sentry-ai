'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ArrowRight, Globe, Activity, Shield, Cpu } from 'lucide-react';

interface SentryLandingProps {
    onStart?: () => void;
}

interface DataNodeProps {
    label: string;
    value: string;
    x: string;
    y: string;
    delay: number;
    align?: 'left' | 'right';
}

/**
 * SentryLanding Component
 * * A high-fidelity, tactical landing page inspired by Palantir's design language.
 * Features:
 * - Mathematical wireframe visualization (parametric cone/spire)
 * - Strict typographic grid
 * - "Wrangling Complexity" aesthetic
 */
export default function SentryLanding({ onStart = () => { } }: SentryLandingProps) {
    const [mounted, setMounted] = useState(false);
    const [scanLine, setScanLine] = useState(0);

    useEffect(() => {
        setMounted(true);
        // Animation loop for the scan line effect
        const interval = setInterval(() => {
            setScanLine(prev => (prev + 1) % 100);
        }, 50);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="relative flex min-h-screen w-full flex-col bg-[#050505] text-white font-sans selection:bg-white selection:text-black overflow-hidden">
            <style>{styles}</style>

            {/* --- BACKGROUND GRID --- */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                {/* Fine grid */}
                <div
                    className="absolute inset-0 opacity-[0.03]"
                    style={{
                        backgroundImage: `linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)`,
                        backgroundSize: '40px 40px'
                    }}
                />
                {/* Radial vignette */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-[#050505]/80" />
            </div>

            {/* --- HEADER METADATA --- */}
            <header className="relative z-20 flex w-full items-start justify-between px-6 py-4 md:px-8 md:py-6 text-[10px] md:text-xs tracking-[0.2em] font-mono text-gray-400">
                <div className="flex items-center gap-3 text-white">
                    <img src="/sentry_logo.svg" alt="Sentry Logo" className="h-8 w-8" />
                    <span className="text-lg font-bold tracking-widest">SENTRY</span>
                </div>

                <div className="hidden md:flex flex-col items-end gap-1 text-right">
                    <a href="#" className="text-white hover:text-white/80 transition-colors duration-300 mb-1">WWW.SENTRY-INTEL.AI</a>
                    <div>TACTICAL + SECURE AG-TECH</div>
                    <div>EST. 2024 / NAIROBI</div>
                    <div>HQ / CLOUD_REGION_1</div>
                </div>
            </header>

            {/* --- MAIN CONTENT LAYER --- */}
            <main className="relative z-10 flex flex-1 flex-col items-center justify-center w-full px-6 py-4">

                {/* THE ARTIFACT (Geometric Visualization) */}
                <div className="relative w-full max-w-6xl aspect-[16/9] flex items-center justify-center">

                    {/* Centerpiece (Spire + Text) - Constrained width */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="relative w-full max-w-3xl aspect-video flex items-center justify-center">
                            {/* Wireframe Geometry */}
                            <WireframeSpire />

                            {/* Typography Overlay */}
                            <div className={`absolute inset-0 flex flex-col items-center justify-center transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                                <div className="relative z-20 mix-blend-difference text-center">
                                    <div className="flex items-center justify-center gap-4 mb-4">
                                        <span className="text-[10px] tracking-[0.3em] font-mono text-white/60">SENTRY OS</span>
                                        <span className="h-px w-12 bg-white/40"></span>
                                        <span className="text-[10px] tracking-[0.3em] font-mono text-white/60">V.2.4.0</span>
                                    </div>

                                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-medium tracking-tighter text-white leading-[0.85]">
                                        SENTRY <br />
                                        <span className="font-light opacity-80">CORE</span>
                                    </h1>

                                    <div className="mt-6 flex flex-col items-center gap-2">
                                        <p className="max-w-md text-center text-xs md:text-sm leading-relaxed tracking-widest text-gray-400 font-mono uppercase">
                                            № 04 / Ingesting Multi-Modal <br />
                                            Agricultural Data
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Decorative Data Nodes - Balanced spacing */}
                    <DataNode label="SENTINEL-2" value="SAT_LINK_ACTIVE" x="5%" y="30%" delay={100} />
                    <DataNode label="DRONE_FLEET" value="STANDBY" x="8%" y="50%" delay={400} />
                    <DataNode label="MARKET_DATA" value="STREAMING" x="5%" y="70%" delay={700} />

                    <DataNode label="IOT_ARRAY" value="CONNECTED" x="85%" y="30%" delay={200} align="right" />
                    <DataNode label="WEATHER_STATION" value="ONLINE" x="82%" y="50%" delay={600} align="right" />
                    <DataNode label="SOIL_SENSORS" value="OPTIMAL" x="85%" y="70%" delay={300} align="right" />

                </div>

                {/* --- ACTION AREA --- */}
                <div className="relative z-30 mt-8 md:mt-12 mb-6">
                    <button
                        onClick={onStart}
                        className="group relative overflow-hidden bg-white text-black px-10 py-4 font-mono text-xs font-bold tracking-[0.2em] transition-all hover:bg-transparent hover:text-white"
                    >
                        <span className="relative z-10 flex items-center gap-3">
                            INITIALIZE_SYSTEM
                            <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
                        </span>
                        {/* Button Hover Fill Effect */}
                        <div className="absolute inset-0 -z-0 bg-white transition-transform duration-300 ease-out group-hover:scale-x-0 group-hover:origin-right" />
                        <div className="absolute inset-0 -z-10 border border-white" />
                    </button>
                </div>

            </main>

            {/* --- FOOTER --- */}
            <footer className="relative z-20 w-full px-6 py-4 md:px-8 md:py-6 border-t border-white/10 flex flex-col md:flex-row items-end md:items-center justify-between gap-4 text-[10px] tracking-[0.2em] font-mono text-gray-500">
                <div className="flex gap-8">
                    <span>© 2025 SENTRY INC</span>
                    <span className="hidden md:inline">PRIVACY PROTOCOLS</span>
                    <span className="hidden md:inline">SYSTEM STATUS</span>
                </div>
                <div className="text-right">
                    <div>INTELLIGENCE FOR THE FIELD</div>
                    <div>POWERED BY SILICON & SOIL</div>
                </div>
            </footer>

        </div>
    );
}

/**
 * WireframeSpire
 * Generates the complex mathematical "cone/teardrop" shape using SVG.
 * Simulates a 3D wireframe object.
 */
function WireframeSpire() {
    // Generate contour lines for a parametric shape (a rounded cone/spire)
    const lines = [];
    const totalLines = 24;

    for (let i = 0; i < totalLines; i++) {
        const progress = i / totalLines;

        // Calculate width at this height (teardrop shape math)
        // Width starts small, gets wide, then tapers to a point
        const y = 10 + (progress * 80); // 10% to 90% height
        const widthFactor = Math.sin(progress * Math.PI) * (1 - (progress * 0.3));
        const rx = 45 * widthFactor; // X radius
        const ry = 12 * widthFactor; // Y radius (perspective foreshortening)

        lines.push(
            <ellipse
                key={i}
                cx="50"
                cy={y}
                rx={rx}
                ry={ry}
                fill="none"
                stroke="currentColor"
                strokeWidth="0.15"
                className="text-white/30 animate-ring-shift"
                style={{
                    opacity: 0.3 + (widthFactor * 0.7), // Fade edges
                    animationDelay: `${i * 0.1}s` // Stagger the animation
                }}
            />
        );
    }

    // Vertical structural lines (Longitudes)
    const verticals = [];
    const numVerticals = 12;
    for (let j = 0; j < numVerticals; j++) {
        // Simple path approximating the curve of the spire
        // In a real 3D engine this would be complex, here we cheat with a path
        const offset = (j / numVerticals) * 100;
        // We aren't drawing real verticals because projecting them to 2D 
        // is hard without a library, so we use a subtle central axis style
    }

    return (
        <svg
            viewBox="0 0 100 100"
            className="absolute inset-0 h-full w-full"
            preserveAspectRatio="xMidYMid meet"
        >
            {/* Central Axis */}
            <line x1="50" y1="0" x2="50" y2="100" stroke="white" strokeWidth="0.1" strokeDasharray="2 2" opacity="0.2" />

            {/* The Horizontal Contours */}
            <g className="origin-center scale-[1.2]">
                {lines}
            </g>


        </svg>
    );
}

/**
 * DataNode
 * A small tactical label positioned absolutely.
 */
function DataNode({ label, value, x, y, delay, align = 'left' }: DataNodeProps) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setVisible(true), delay);
        return () => clearTimeout(timer);
    }, [delay]);

    return (
        <div
            className={`absolute flex flex-col gap-1 transition-all duration-1000 ${visible ? 'opacity-100' : 'opacity-0 translate-y-4'}`}
            style={{
                left: x,
                top: y,
                alignItems: align === 'right' ? 'flex-end' : 'flex-start',
                textAlign: align === 'right' ? 'right' : 'left'
            }}
        >
            <div className="flex items-center gap-2">
                {align === 'right' && <span className="text-xs md:text-sm font-bold tracking-widest text-white">{label}</span>}
                <div className="h-2 w-2 bg-white border border-white shadow-[0_0_10px_rgba(255,255,255,0.5)]" />
                {align === 'left' && <span className="text-xs md:text-sm font-bold tracking-widest text-white">{label}</span>}
            </div>
            <div className="font-mono text-[10px] md:text-xs text-gray-400 tracking-widest pl-4 border-l border-gray-700">
                {value}
            </div>
        </div>
    )
}

// Add strict animations via style tag since we can't configure tailwind config here
const styles = `
  @keyframes scan-vertical {
    0% { transform: translateY(-30px) scale(0.8); opacity: 0; }
    20% { opacity: 1; }
    80% { opacity: 1; }
    100% { transform: translateY(30px) scale(0.2); opacity: 0; }
  }
  .animate-scan-vertical {
    animation: scan-vertical 4s ease-in-out infinite;
  }
  @keyframes ring-shift {
    0% { stroke-dashoffset: 0; }
    100% { stroke-dashoffset: 100; }
  }
  .animate-ring-shift {
    stroke-dasharray: 5 5;
    animation: ring-shift 8s linear infinite;
  }
`;