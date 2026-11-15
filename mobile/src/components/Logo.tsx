import React from 'react';
import Svg, { Path, Circle } from 'react-native-svg';

// Aproximación del símbolo TrueMatch AI dibujada en SVG.
// Si quieres el original exacto, exporta el símbolo desde Figma como SVG
// y reemplaza este componente.
export default function Logo({ size = 96 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 96 96" fill="none">
      <Path
        d="M79 36.7 A33 33 0 1 1 53.7 15.5"
        stroke="#FFFFFF"
        strokeWidth={5}
        strokeLinecap="round"
      />
      <Path
        d="M53.7 15.5 A33 33 0 0 1 79 36.7"
        stroke="#A5ECF5"
        strokeWidth={5}
        strokeLinecap="round"
      />
      <Path d="M47 37 L70 28" stroke="#A5ECF5" strokeWidth={4} strokeLinecap="round" />
      <Circle cx={47} cy={37} r={6} fill="#A5ECF5" />
      <Path
        d="M35 62 C35 53 40 50 48 50 C56 50 61 53 61 62"
        stroke="#FFFFFF"
        strokeWidth={5}
        strokeLinecap="round"
      />
    </Svg>
  );
}