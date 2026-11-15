import React from 'react';
import { View, Text, ScrollView, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import PrimaryButton from '../components/PrimaryButton';
import { colors } from '../theme';

type Props = { onNext: () => void };

// Datos ilustrativos (igual que en el prototipo de Figma)
const AFINIDAD = [
  { label: 'Audiencia objetivo', v: 92 },
  { label: 'Contenido premium', v: 88 },
  { label: 'Engagement activo', v: 76 },
  { label: 'Tonos de voz', v: 94 },
];

export default function ReporteScreen({ onNext }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={{ gap: 8 }}>
          <Text style={styles.title}>Reporte de concordancia</Text>
          <Text style={styles.sub}>Análisis ilustrativo para una campaña automotriz</Text>
        </View>

        <View style={styles.block}>
          <View style={styles.highlight}>
            <View style={styles.bigWrap}>
              <Text style={styles.big}>85%</Text>
              <Text style={styles.matchLabel}>Match</Text>
            </View>
            <View style={styles.highlightText}>
              <Text style={styles.highlightTitle}>Concordancia con Marca de Autos</Text>
              <Text style={styles.highlightBody}>
                El perfil coincide con el tono, el público objetivo y la narrativa de la marca.
              </Text>
            </View>
          </View>
        </View>

        <View style={[styles.block, { gap: 16 }]}>
          <Text style={styles.blockTitle}>Afinidad comparativa</Text>
          {AFINIDAD.map((a) => (
            <View key={a.label} style={{ gap: 8 }}>
              <View style={styles.row}>
                <Text style={styles.metric}>{a.label}</Text>
                <Text style={styles.metricValue}>{a.v}%</Text>
              </View>
              <View style={styles.track}>
                <View style={[styles.fill, { width: `${a.v}%` }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={[styles.block, { gap: 16 }]}>
          <Text style={styles.blockTitle}>Conclusiones</Text>
          <Text style={styles.body}>
            El perfil presenta una alta concordancia con la marca de autos debido a su audiencia
            objetivo, contenido premium y tonos de voz coherentes. Aunque el engagement activo es
            ligeramente inferior, el resultado general lo convierte en un candidato sólido para una
            campaña de lanzamiento o experiencia de marca.
          </Text>
        </View>

        <PrimaryButton label="Ver Sectores Compatibles" height={51} onPress={onNext} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 24, gap: 12 },
  title: { fontSize: 28, fontWeight: '700', color: colors.text },
  sub: { fontSize: 14, color: colors.textMuted },
  block: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 20,
    padding: 16,
  },
  highlight: {
    backgroundColor: colors.blueSoft,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  bigWrap: { gap: 2 },
  big: { fontSize: 48, fontWeight: '700', color: colors.blue },
  matchLabel: { fontSize: 12, fontWeight: '600', color: colors.blue },
  highlightText: { flex: 1, gap: 6 },
  highlightTitle: { fontSize: 18, fontWeight: '700', color: colors.text },
  highlightBody: { fontSize: 13, color: colors.textMuted },
  blockTitle: { fontSize: 18, fontWeight: '700', color: colors.text },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  metric: { fontSize: 14, fontWeight: '600', color: colors.textSoft },
  metricValue: { fontSize: 14, fontWeight: '700', color: colors.blue },
  track: { height: 10, borderRadius: 999, backgroundColor: colors.border, overflow: 'hidden' },
  fill: { height: 10, borderRadius: 999, backgroundColor: colors.blue },
  body: { fontSize: 14, lineHeight: 22, color: colors.textMuted },
});