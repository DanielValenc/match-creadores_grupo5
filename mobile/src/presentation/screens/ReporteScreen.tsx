import React from 'react';
import { View, Text, ScrollView, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MessageCircle } from 'lucide-react-native';
import PrimaryButton from '../components/PrimaryButton';
import { colors } from '../theme';
import { useCreatorAnalysis } from '../hooks/useCreatorAnalysis';
import type { AudienceAudit } from '../../domain/audience-audit/AudienceAudit';
import {
  DEFAULT_AUDIT_DISCLAIMER,
  MIN_AUDIT_SAMPLE_SIZE,
} from '../../domain/audience-audit/AudienceAudit';

type Props = { onNext: () => void };

function textoMuestra(audit: AudienceAudit): string {
  if (audit.sampleSize === null) return 'No se pudo determinar el tamaño de la muestra.';
  const total = audit.totalRecords !== null ? ` de ${audit.totalRecords} registros` : '';
  return `${audit.sampleSize} valores válidos${total} (mínimo recomendado: ${MIN_AUDIT_SAMPLE_SIZE}).`;
}

export default function ReporteScreen({ onNext }: Props) {
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

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={{ gap: 8 }}>
          <Text style={styles.title}>Reporte de concordancia</Text>
          <Text style={styles.sub}>Perfil comercial de @{creator.username}</Text>
        </View>

        <View style={styles.block}>
          <View style={styles.highlight}>
            <View style={styles.iconWrap}>
              <MessageCircle size={28} color={colors.blue} />
            </View>
            <View style={styles.highlightText}>
              <Text style={styles.highlightTitle}>Tono de comunicación</Text>
              <Text style={styles.highlightBody}>
                {creator.communicationTone ?? 'La IA no identificó un tono de comunicación.'}
              </Text>
            </View>
          </View>
        </View>

        <View style={[styles.block, { gap: 16 }]}>
          <Text style={styles.blockTitle}>Intereses</Text>
          {creator.interests.length === 0 ? (
            <Text style={styles.body}>La IA no identificó intereses para este perfil.</Text>
          ) : (
            <View style={styles.chips}>
              {creator.interests.map((interes, i) => (
                <View key={`${interes}-${i}`} style={styles.chip}>
                  <Text style={styles.chipText}>{interes}</Text>
                </View>
              ))}
            </View>
          )}
        </View>

        <View style={[styles.block, { gap: 16 }]}>
          <Text style={styles.blockTitle}>Auditoría de audiencia</Text>
          {!audit ? (
            <Text style={styles.body}>El análisis no incluye la auditoría de audiencia.</Text>
          ) : (
            <>
              <View style={{ gap: 4 }}>
                <Text style={styles.metric}>Tamaño de la muestra</Text>
                <Text style={styles.body}>{textoMuestra(audit)}</Text>
              </View>
              <View style={{ gap: 4 }}>
                <Text style={styles.metric}>Advertencias</Text>
                {audit.warnings.length === 0 ? (
                  <Text style={styles.body}>Sin advertencias.</Text>
                ) : (
                  audit.warnings.map((w, i) => (
                    <Text key={i} style={styles.body}>
                      • {w}
                    </Text>
                  ))
                )}
              </View>
            </>
          )}
          <Text style={styles.note}>{audit?.disclaimer ?? DEFAULT_AUDIT_DISCLAIMER}</Text>
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
  iconWrap: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  highlightText: { flex: 1, gap: 6 },
  highlightTitle: { fontSize: 18, fontWeight: '700', color: colors.text },
  highlightBody: { fontSize: 14, lineHeight: 20, color: colors.textSoft },
  blockTitle: { fontSize: 18, fontWeight: '700', color: colors.text },
  metric: { fontSize: 14, fontWeight: '600', color: colors.textSoft },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    backgroundColor: colors.blueSoft,
    borderRadius: 999,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  chipText: { fontSize: 13, fontWeight: '600', color: colors.blue },
  body: { fontSize: 14, lineHeight: 22, color: colors.textMuted },
  note: { fontSize: 12, lineHeight: 18, color: colors.placeholder, fontStyle: 'italic' },
});
