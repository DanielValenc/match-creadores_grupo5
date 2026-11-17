import React from 'react';
import { View, Text, ScrollView, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Path, Line } from 'react-native-svg';
import { User } from 'lucide-react-native';
import PrimaryButton from '../components/PrimaryButton';
import { colors } from '../theme';

type BigFive = {
  Apertura?: number;
  Responsabilidad?: number;
  Extraversion?: number;
  Amabilidad?: number;
  Neuroticismo?: number;
};

type Props = {
  nombre?: string;
  bigFive?: BigFive;
  resumen?: string;
  onNext: () => void;
};

const RESUMEN_DEFAULT =
  'Influencer sociable, creativo y cercano. Destaca por su apertura y extraversión, lo que sugiere una personalidad comunicativa y abierta a nuevas ideas. Su amabilidad moderada indica una conexión empática con su audiencia, mientras que su neuroticismo bajo sugiere una mayor estabilidad emocional.';

// Curva ilustrativa de la Ley de Benford (viewBox 313 x 160)
const PUNTOS: [number, number][] = [
  [0, 158], [35, 145], [70, 105], [100, 98], [135, 85],
  [155, 65], [190, 35], [240, 32], [290, 12], [312, 1],
];

function suave(p: [number, number][]) {
  let d = `M${p[0][0]} ${p[0][1]}`;
  for (let i = 0; i < p.length - 1; i++) {
    const p0 = p[i - 1] ?? p[i];
    const p1 = p[i];
    const p2 = p[i + 1];
    const p3 = p[i + 2] ?? p2;
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C${c1x} ${c1y} ${c2x} ${c2y} ${p2[0]} ${p2[1]}`;
  }
  return d;
}

export default function DashboardScreen({
  nombre = 'Daniel',
  bigFive,
  resumen,
  onNext,
}: Props) {
  const rasgos = [
    { label: 'Apertura', v: bigFive?.Apertura ?? 23 },
    { label: 'Conciencia', v: bigFive?.Responsabilidad ?? 19 },
    { label: 'Extraversión', v: bigFive?.Extraversion ?? 25 },
    { label: 'Amabilidad', v: bigFive?.Amabilidad ?? 21 },
    { label: 'Neuroticismo', v: bigFive?.Neuroticismo ?? 12 },
  ];

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={{ gap: 4 }}>
            <Text style={styles.hello}>Hola, {nombre}</Text>
            <Text style={styles.sub}>Resumen de hoy</Text>
          </View>
          <View style={styles.avatar}>
            <User size={24} color={colors.indigo} />
          </View>
        </View>

        <View style={styles.card}>
          <View style={{ gap: 4 }}>
            <Text style={styles.cardTitle}>Autenticidad de Audiencia (Ley de Benford)</Text>
            <Text style={styles.organic}>95% Audiencia Orgánica</Text>
          </View>
          <View style={styles.chart}>
            <Svg width="100%" height={160} viewBox="0 0 313 160" preserveAspectRatio="none">
              {[0.5, 80, 159.5].map((y) => (
                <Line
                  key={y}
                  x1={0}
                  x2={313}
                  y1={y}
                  y2={y}
                  stroke={colors.border}
                  strokeWidth={1}
                  strokeDasharray="4 4"
                />
              ))}
              <Path
                d={suave(PUNTOS)}
                stroke={colors.indigo}
                strokeWidth={3}
                strokeLinecap="round"
                fill="none"
              />
            </Svg>
          </View>
          <View style={styles.axis}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
              <Text key={n} style={styles.axisText}>
                {n}
              </Text>
            ))}
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Análisis Psicológico (Big Five)</Text>
          <View style={{ gap: 12 }}>
            {rasgos.map((r) => (
              <View key={r.label} style={{ gap: 8 }}>
                <View style={styles.row}>
                  <Text style={styles.rasgo}>{r.label}</Text>
                  <Text style={styles.rasgoValue}>{r.v}%</Text>
                </View>
                <View style={styles.track}>
                  <View style={[styles.fill, { width: `${r.v}%` }]} />
                </View>
              </View>
            ))}
            <View style={styles.perfil}>
              <Text style={styles.perfilLabel}>Perfil ilustrativo</Text>
              <Text style={styles.perfilText}>{resumen || RESUMEN_DEFAULT}</Text>
            </View>
          </View>
        </View>

        <PrimaryButton
          label="Ver Concordancia con Marcas"
          backgroundColor={colors.indigo}
          height={51}
          onPress={onNext}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { paddingHorizontal: 24, paddingTop: 24, paddingBottom: 24, gap: 16 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  hello: { fontSize: 28, fontWeight: '700', color: colors.text },
  sub: { fontSize: 14, color: colors.textMuted },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.indigoSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 16,
    gap: 16,
  },
  cardTitle: { fontSize: 16, fontWeight: '600', color: colors.text },
  organic: { fontSize: 13, fontWeight: '600', color: colors.green },
  chart: {
    height: 160,
    backgroundColor: colors.bg,
    borderRadius: 12,
    overflow: 'hidden',
  },
  axis: { flexDirection: 'row', justifyContent: 'space-between' },
  axisText: { fontSize: 12, color: colors.textMuted },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  rasgo: { fontSize: 14, fontWeight: '500', color: colors.text },
  rasgoValue: { fontSize: 14, fontWeight: '600', color: colors.indigo },
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.gray100,
    overflow: 'hidden',
  },
  fill: { height: 8, borderRadius: 4, backgroundColor: colors.indigo },
  perfil: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
  perfilLabel: { fontSize: 12, fontWeight: '600', color: colors.textMuted },
  perfilText: { fontSize: 13, lineHeight: 18, color: colors.text },
});