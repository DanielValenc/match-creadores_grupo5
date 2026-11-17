import React from "react";
import { View, Text, ScrollView, StyleSheet, StatusBar } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { User } from "lucide-react-native";
import PrimaryButton from "../components/PrimaryButton";
import { colors } from "../theme";
import type { Documento } from "../services/api";

type Props = {
  datos: Documento | null;
  onNext: () => void;
};

function formatNumber(value?: number | null): string {
  if (value === null || value === undefined || !Number.isFinite(value))
    return "No disponible";
  return new Intl.NumberFormat("es-EC").format(value);
}

function ScoreRow({ label, value }: { label: string; value?: number | null }) {
  const available = typeof value === "number" && Number.isFinite(value);
  const safeValue = available ? Math.max(0, Math.min(100, value)) : 0;

  return (
    <View style={{ gap: 8 }}>
      <View style={styles.row}>
        <Text style={styles.rasgo}>{label}</Text>
        <Text style={styles.rasgoValue}>
          {available ? `${safeValue}/100` : "Sin evidencia suficiente"}
        </Text>
      </View>
      <View style={styles.track}>
        {available && (
          <View style={[styles.fill, { width: `${safeValue}%` }]} />
        )}
      </View>
    </View>
  );
}

export default function DashboardScreen({ datos, onNext }: Props) {
  const bigFive = datos?.analisis_bigfive;
  const audit = datos?.auditoria_audiencia;
  const profile = datos?.perfil;
  const nombre = datos?.usuario ? `@${datos.usuario}` : "creador";
  const organic = audit?.puntaje_organico;

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View style={{ gap: 4, flex: 1 }}>
            <Text style={styles.hello}>Hola, {nombre}</Text>
            <Text style={styles.sub}>
              Resultados del análisis de TrueMatch AI
            </Text>
          </View>
          <View style={styles.avatar}>
            <User size={24} color={colors.indigo} />
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Resumen del creador</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>
                {formatNumber(profile?.seguidores)}
              </Text>
              <Text style={styles.statLabel}>Seguidores</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>
                {formatNumber(profile?.siguiendo)}
              </Text>
              <Text style={styles.statLabel}>Siguiendo</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>
                {formatNumber(profile?.me_gusta)}
              </Text>
              <Text style={styles.statLabel}>Me gusta</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>
                {formatNumber(datos?.videos_recientes?.length)}
              </Text>
              <Text style={styles.statLabel}>Videos analizados</Text>
            </View>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>
            Auditoría de audiencia · Ley de Benford
          </Text>
          <Text style={styles.organic}>
            {organic === null || organic === undefined
              ? "Puntaje orgánico no disponible"
              : `${organic}% · Puntaje orgánico estimado`}
          </Text>
          <Text style={styles.description}>
            {audit
              ? `Muestra válida: ${formatNumber(audit.tamano_muestra)} registros de ${formatNumber(audit.registros_totales)}. ` +
                `${formatNumber(audit.ordenes_de_magnitud)} órdenes de magnitud.`
              : "Todavía no hay datos de auditoría disponibles para este perfil."}
          </Text>
          <Text style={styles.smallNote}>
            La desviación respecto de Benford no demuestra por sí sola
            seguidores falsos ni fraude.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>
            Análisis de personalidad · Big Five
          </Text>
          <View style={{ gap: 14 }}>
            <ScoreRow label="Apertura" value={bigFive?.Apertura} />
            <ScoreRow
              label="Responsabilidad"
              value={bigFive?.Responsabilidad}
            />
            <ScoreRow label="Extraversión" value={bigFive?.Extraversion} />
            <ScoreRow label="Amabilidad" value={bigFive?.Amabilidad} />
            <ScoreRow label="Neuroticismo" value={bigFive?.Neuroticismo} />
          </View>
          <View style={styles.perfil}>
            <Text style={styles.perfilLabel}>Resumen generado por IA</Text>
            <Text style={styles.perfilText}>
              {bigFive?.resumen?.trim() ||
                "El backend no devolvió un resumen de personalidad."}
            </Text>
          </View>
          <Text style={styles.smallNote}>
            Estos resultados son estimaciones orientativas basadas en contenido
            público, no un test psicológico validado.
          </Text>
        </View>

        <PrimaryButton
          label="Ver reporte de auditoría"
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
  content: {
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 28,
    gap: 16,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  hello: { fontSize: 25, fontWeight: "700", color: colors.text },
  sub: { fontSize: 13, color: colors.textMuted },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.indigoSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 16,
    gap: 14,
  },
  cardTitle: { fontSize: 16, fontWeight: "700", color: colors.text },
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  statBox: {
    width: "48%",
    flexGrow: 1,
    backgroundColor: colors.bg,
    borderRadius: 12,
    padding: 12,
    gap: 4,
  },
  statValue: { fontSize: 17, fontWeight: "700", color: colors.indigo },
  statLabel: { fontSize: 12, color: colors.textMuted },
  organic: { fontSize: 16, fontWeight: "700", color: colors.green },
  description: { fontSize: 13, color: colors.textSoft, lineHeight: 19 },
  smallNote: { fontSize: 11, color: colors.textMuted, lineHeight: 16 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 8,
  },
  rasgo: { fontSize: 13, fontWeight: "500", color: colors.textSoft },
  rasgoValue: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.indigo,
    textAlign: "right",
    flexShrink: 1,
  },
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.gray100,
    overflow: "hidden",
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
  perfilLabel: { fontSize: 12, fontWeight: "700", color: colors.textMuted },
  perfilText: { fontSize: 13, lineHeight: 19, color: colors.text },
});
