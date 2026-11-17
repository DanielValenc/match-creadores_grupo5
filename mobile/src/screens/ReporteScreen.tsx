import React from "react";
import { View, Text, ScrollView, StyleSheet, StatusBar } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import PrimaryButton from "../components/PrimaryButton";
import { colors } from "../theme";
import type { AuditoriaAudiencia } from "../services/api";

type Props = {
  auditoria?: AuditoriaAudiencia;
  onNext: () => void;
};

function number(value?: number | null, decimals = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value))
    return "No disponible";
  return value.toFixed(decimals);
}

function DistributionRow({
  digit,
  observed,
  expected,
}: {
  digit: number;
  observed: number | null;
  expected: number;
}) {
  const observedWidth =
    observed === null ? 0 : Math.max(0, Math.min(100, observed));
  const expectedWidth = Math.max(0, Math.min(100, expected));

  return (
    <View style={styles.distributionRow}>
      <Text style={styles.digit}>{digit}</Text>
      <View style={styles.distributionBars}>
        <View style={styles.barLine}>
          <Text style={styles.barLabel}>Observado</Text>
          <View style={styles.track}>
            {observed !== null && (
              <View
                style={[styles.observedFill, { width: `${observedWidth}%` }]}
              />
            )}
          </View>
          <Text style={styles.percent}>
            {observed === null ? "—" : `${number(observed, 1)}%`}
          </Text>
        </View>
        <View style={styles.barLine}>
          <Text style={styles.barLabel}>Benford</Text>
          <View style={styles.track}>
            <View
              style={[styles.expectedFill, { width: `${expectedWidth}%` }]}
            />
          </View>
          <Text style={styles.percent}>{number(expected, 1)}%</Text>
        </View>
      </View>
    </View>
  );
}

export default function ReporteScreen({ auditoria, onNext }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={{ gap: 8 }}>
          <Text style={styles.title}>Reporte de auditoría</Text>
          <Text style={styles.sub}>
            Distribución observada frente a la distribución teórica de Benford.
          </Text>
        </View>

        {!auditoria ? (
          <View style={styles.block}>
            <Text style={styles.blockTitle}>No hay auditoría disponible</Text>
            <Text style={styles.body}>
              El backend no entregó el bloque auditoria_audiencia para este
              perfil.
            </Text>
          </View>
        ) : (
          <>
            <View style={styles.highlight}>
              <View style={styles.scoreWrap}>
                <Text style={styles.big}>
                  {auditoria.puntaje_organico === null
                    ? "—"
                    : `${auditoria.puntaje_organico}%`}
                </Text>
                <Text style={styles.matchLabel}>Puntaje orgánico</Text>
              </View>
              <Text style={styles.highlightBody}>
                {auditoria.puntaje_organico === null
                  ? "No se pudo calcular un puntaje con la muestra disponible."
                  : "Puntaje descriptivo calculado por la política de auditoría de TrueMatch."}
              </Text>
            </View>

            <View style={styles.block}>
              <Text style={styles.blockTitle}>Resumen de la muestra</Text>
              <View style={styles.summaryGrid}>
                <View style={styles.summaryCell}>
                  <Text style={styles.summaryValue}>
                    {auditoria.tamano_muestra}
                  </Text>
                  <Text style={styles.summaryLabel}>Registros válidos</Text>
                </View>
                <View style={styles.summaryCell}>
                  <Text style={styles.summaryValue}>
                    {auditoria.registros_totales}
                  </Text>
                  <Text style={styles.summaryLabel}>Registros totales</Text>
                </View>
                <View style={styles.summaryCell}>
                  <Text style={styles.summaryValue}>
                    {number(auditoria.mad, 4)}
                  </Text>
                  <Text style={styles.summaryLabel}>MAD</Text>
                </View>
                <View style={styles.summaryCell}>
                  <Text style={styles.summaryValue}>
                    {auditoria.ordenes_de_magnitud}
                  </Text>
                  <Text style={styles.summaryLabel}>Órdenes de magnitud</Text>
                </View>
              </View>
            </View>

            <View style={styles.block}>
              <Text style={styles.blockTitle}>Primer dígito significativo</Text>
              <Text style={styles.body}>
                Comparación de la proporción observada con la esperada según
                Benford.
              </Text>
              {auditoria.distribucion?.length ? (
                <View style={{ gap: 14, marginTop: 8 }}>
                  {auditoria.distribucion.map((item) => (
                    <DistributionRow
                      key={item.digito}
                      digit={item.digito}
                      observed={item.observado_porcentaje}
                      expected={item.esperado_porcentaje}
                    />
                  ))}
                </View>
              ) : (
                <Text style={styles.body}>
                  El backend no devolvió la distribución por dígito.
                </Text>
              )}
            </View>

            <View style={styles.block}>
              <Text style={styles.blockTitle}>Registros excluidos</Text>
              {Object.entries(auditoria.excluidos || {}).length ? (
                Object.entries(auditoria.excluidos).map(([key, value]) => (
                  <View key={key} style={styles.listRow}>
                    <Text style={styles.body}>{key}</Text>
                    <Text style={styles.listValue}>{value}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.body}>No se informaron exclusiones.</Text>
              )}
            </View>

            {!!auditoria.advertencias?.length && (
              <View style={styles.block}>
                <Text style={styles.blockTitle}>Advertencias</Text>
                {auditoria.advertencias.map((warning, index) => (
                  <Text key={`${index}-${warning}`} style={styles.body}>
                    • {warning}
                  </Text>
                ))}
              </View>
            )}

            {!!auditoria.disclaimer && (
              <View style={styles.disclaimer}>
                <Text style={styles.disclaimerTitle}>Interpretación</Text>
                <Text style={styles.body}>{auditoria.disclaimer}</Text>
              </View>
            )}
          </>
        )}

        <PrimaryButton
          label="Ver sectores compatibles"
          height={51}
          onPress={onNext}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 24, gap: 14, paddingBottom: 32 },
  title: { fontSize: 28, fontWeight: "700", color: colors.text },
  sub: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  block: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 18,
    padding: 16,
    gap: 14,
  },
  blockTitle: { fontSize: 17, fontWeight: "700", color: colors.text },
  highlight: {
    backgroundColor: colors.blueSoft,
    borderRadius: 16,
    padding: 18,
    gap: 10,
  },
  scoreWrap: { gap: 2 },
  big: { fontSize: 42, fontWeight: "800", color: colors.blue },
  matchLabel: { fontSize: 12, fontWeight: "700", color: colors.blue },
  highlightBody: { fontSize: 13, lineHeight: 19, color: colors.textSoft },
  summaryGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  summaryCell: {
    width: "47%",
    flexGrow: 1,
    backgroundColor: colors.bg,
    borderRadius: 12,
    padding: 12,
    gap: 4,
  },
  summaryValue: { fontSize: 18, fontWeight: "700", color: colors.indigo },
  summaryLabel: { fontSize: 11, color: colors.textMuted },
  body: { fontSize: 13, lineHeight: 19, color: colors.textMuted },
  distributionRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  digit: { width: 18, fontSize: 16, fontWeight: "700", color: colors.text },
  distributionBars: { flex: 1, gap: 8 },
  barLine: { flexDirection: "row", alignItems: "center", gap: 7 },
  barLabel: { width: 68, fontSize: 10, color: colors.textMuted },
  track: {
    flex: 1,
    height: 8,
    borderRadius: 5,
    backgroundColor: colors.gray100,
    overflow: "hidden",
  },
  observedFill: { height: 8, backgroundColor: colors.indigo, borderRadius: 5 },
  expectedFill: { height: 8, backgroundColor: colors.green, borderRadius: 5 },
  percent: {
    width: 43,
    fontSize: 10,
    textAlign: "right",
    color: colors.textSoft,
  },
  listRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  listValue: { fontSize: 13, fontWeight: "700", color: colors.text },
  disclaimer: {
    backgroundColor: colors.gray100,
    borderRadius: 14,
    padding: 15,
    gap: 8,
  },
  disclaimerTitle: { fontSize: 14, fontWeight: "700", color: colors.text },
});
