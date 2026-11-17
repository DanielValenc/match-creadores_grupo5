import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, StatusBar, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Path, Line } from 'react-native-svg';
import { User } from 'lucide-react-native';
import PrimaryButton from '../components/PrimaryButton';
import { colors } from '../theme';
import { useCreatorAnalysis } from '../hooks/useCreatorAnalysis';
import type { AudienceAudit } from '../../domain/audience-audit/AudienceAudit';
import { MIN_AUDIT_SAMPLE_SIZE } from '../../domain/audience-audit/AudienceAudit';
import type { BigFiveTrait } from '../../domain/creator-profiling/BigFiveProfile';
import { BIG_FIVE_TRAITS } from '../../domain/creator-profiling/BigFiveProfile';

type Props = { onNext: () => void };

const AUDIT_SHORT_NOTE = 'Indicador estadístico. No prueba fraude ni autenticidad.';

const TRAIT_LABELS: Record<BigFiveTrait, string> = {
  openness: 'Apertura',
  conscientiousness: 'Responsabilidad',
  extraversion: 'Extraversión',
  agreeableness: 'Amabilidad',
  neuroticism: 'Neuroticismo',
};

// Área del gráfico (viewBox 313 x 160), con margen para que la curva no se corte.
const CHART_W = 313;
const CHART_H = 160;
const CHART_PAD = 12;

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

/** Curvas observada y esperada (en % por dígito 1-9), o null si no hay distribución completa. */
function benfordPaths(audit: AudienceAudit | null) {
  const digits = [...(audit?.distribution ?? [])]
    .filter((d) => d.digit >= 1 && d.digit <= 9)
    .sort((a, b) => a.digit - b.digit);
  if (digits.length < 2) return null;
  const max = Math.max(...digits.flatMap((d) => [d.observedPercent, d.expectedPercent]), 1);
  const toPoints = (pick: (d: (typeof digits)[number]) => number): [number, number][] =>
    digits.map((d) => [
      ((d.digit - 1) / 8) * CHART_W,
      CHART_H - CHART_PAD - (pick(d) / max) * (CHART_H - 2 * CHART_PAD),
    ]);
  return {
    observed: suave(toPoints((d) => d.observedPercent)),
    expected: suave(toPoints((d) => d.expectedPercent)),
  };
}

/** Explica por qué no hay puntaje orgánico. */
function motivoSinPuntaje(audit: AudienceAudit | null): string {
  if (!audit) return 'El análisis no incluye la auditoría de audiencia.';
  if (audit.sampleSize === null) {
    return `No se pudo determinar cuántos valores válidos hay; se necesitan ${MIN_AUDIT_SAMPLE_SIZE}.`;
  }
  if (audit.sampleSize < MIN_AUDIT_SAMPLE_SIZE) {
    return `Muestra insuficiente: ${audit.sampleSize} valores válidos de ${MIN_AUDIT_SAMPLE_SIZE} necesarios.`;
  }
  return audit.warnings[0] ?? 'La muestra no permite calcular el puntaje.';
}

function Avatar({ uri }: { uri: string | null }) {
  // Las URLs de TikTok caducan: si la imagen falla, se muestra el ícono.
  const [failed, setFailed] = useState(false);
  return (
    <View style={styles.avatar}>
      {uri && !failed ? (
        <Image source={{ uri }} style={styles.avatarImg} onError={() => setFailed(true)} />
      ) : (
        <User size={24} color={colors.indigo} />
      )}
    </View>
  );
}

export default function DashboardScreen({ onNext }: Props) {
  const { creator } = useCreatorAnalysis();

  if (!creator) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.content}>
          <Text style={styles.sub}>No hay un análisis cargado.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const audit = creator.audit;
  const score = audit?.organicScore ?? null;
  const curvas = benfordPaths(audit);
  const rasgos = BIG_FIVE_TRAITS.map((t) => ({
    key: t,
    label: TRAIT_LABELS[t],
    v: creator.bigFive.traits[t].score,
  }));

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.hello} numberOfLines={1}>
              @{creator.username}
            </Text>
            <Text style={styles.sub}>Resultado del análisis</Text>
          </View>
          <Avatar uri={creator.profile.avatarUrl} />
        </View>

        <View style={styles.card}>
          <View style={{ gap: 4 }}>
            <Text style={styles.cardTitle}>Autenticidad de Audiencia (Ley de Benford)</Text>
            {score !== null ? (
              <Text style={styles.organic}>Puntaje orgánico: {Math.round(score)}/100</Text>
            ) : (
              <>
                <Text style={styles.noScore}>Sin puntaje</Text>
                <Text style={styles.note}>{motivoSinPuntaje(audit)}</Text>
              </>
            )}
          </View>
          <View style={styles.chart}>
            {curvas ? (
              <Svg
                width="100%"
                height={CHART_H}
                viewBox={`0 0 ${CHART_W} ${CHART_H}`}
                preserveAspectRatio="none"
              >
                {[0.5, 80, 159.5].map((y) => (
                  <Line
                    key={y}
                    x1={0}
                    x2={CHART_W}
                    y1={y}
                    y2={y}
                    stroke={colors.border}
                    strokeWidth={1}
                    strokeDasharray="4 4"
                  />
                ))}
                <Path
                  d={curvas.expected}
                  stroke={colors.placeholder}
                  strokeWidth={2}
                  strokeDasharray="6 4"
                  fill="none"
                />
                <Path
                  d={curvas.observed}
                  stroke={colors.indigo}
                  strokeWidth={3}
                  strokeLinecap="round"
                  fill="none"
                />
              </Svg>
            ) : (
              <View style={styles.chartEmpty}>
                <Text style={styles.note}>Sin datos de distribución por dígito.</Text>
              </View>
            )}
          </View>
          <View style={styles.axis}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
              <Text key={n} style={styles.axisText}>
                {n}
              </Text>
            ))}
          </View>
          {curvas && (
            <View style={styles.legend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendLine, { backgroundColor: colors.indigo }]} />
                <Text style={styles.axisText}>Observado</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendLine, { backgroundColor: colors.placeholder }]} />
                <Text style={styles.axisText}>Esperado (Benford)</Text>
              </View>
              <Text style={styles.axisText}>% por primer dígito</Text>
            </View>
          )}
          <Text style={styles.note}>{AUDIT_SHORT_NOTE}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Análisis Psicológico (Big Five)</Text>
          <View style={{ gap: 12 }}>
            {rasgos.map((r) => (
              <View key={r.key} style={{ gap: 8 }}>
                <View style={styles.row}>
                  <Text style={styles.rasgo}>{r.label}</Text>
                  {r.v !== null ? (
                    <Text style={styles.rasgoValue}>{Math.round(r.v)}%</Text>
                  ) : (
                    <Text style={styles.rasgoMissing}>Evidencia insuficiente</Text>
                  )}
                </View>
                <View style={styles.track}>
                  {r.v !== null && <View style={[styles.fill, { width: `${r.v}%` }]} />}
                </View>
              </View>
            ))}
            <View style={styles.perfil}>
              <Text style={styles.perfilLabel}>Resumen generado por IA, no verificado</Text>
              <Text style={styles.perfilText}>
                {creator.bigFive.summary ?? 'La IA no generó un resumen para este perfil.'}
              </Text>
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
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  headerText: { flex: 1, gap: 4 },
  hello: { fontSize: 28, fontWeight: '700', color: colors.text },
  sub: { fontSize: 14, color: colors.textMuted },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.indigoSoft,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarImg: { width: 48, height: 48 },
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
  noScore: { fontSize: 13, fontWeight: '600', color: colors.textGray },
  note: { fontSize: 12, lineHeight: 16, color: colors.textMuted },
  chartEmpty: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 12 },
  legend: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendLine: { width: 16, height: 3, borderRadius: 2 },
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
  rasgoMissing: { fontSize: 13, fontWeight: '500', color: colors.textMuted },
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