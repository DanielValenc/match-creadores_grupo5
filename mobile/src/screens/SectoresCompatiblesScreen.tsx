import React from "react";
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  ScrollView,
  StatusBar,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors } from "../theme";
import type { PerfilComercial } from "../api";

type Props = {
  perfilComercial?: PerfilComercial;
  onContact?: () => void;
  onCancel?: () => void;
};

function AffinityCard({
  categoria,
  motivo,
}: {
  categoria: string;
  motivo: string;
}) {
  return (
    <View style={styles.card}>
      <View style={styles.categoryMark}>
        <Text style={styles.categoryInitial}>
          {categoria.trim().charAt(0).toUpperCase() || "•"}
        </Text>
      </View>
      <View style={styles.cardContent}>
        <Text style={styles.cardName}>{categoria}</Text>
        <Text style={styles.cardReason}>
          {motivo ||
            "El backend no proporcionó una justificación para esta afinidad."}
        </Text>
      </View>
    </View>
  );
}

export default function SectoresCompatiblesScreen({
  perfilComercial,
  onContact,
  onCancel,
}: Props) {
  const affinities = perfilComercial?.afinidad_marcas ?? [];
  const interests = perfilComercial?.intereses ?? [];
  const tone = perfilComercial?.tono_comunicacion?.trim();

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <StatusBar barStyle="dark-content" />
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Sectores compatibles</Text>
          <Text style={styles.subtitle}>
            Afinidades identificadas por el análisis de contenido del creador.
          </Text>
        </View>

        <View style={styles.infoBlock}>
          <Text style={styles.sectionTitle}>Tono de comunicación</Text>
          <Text style={styles.description}>
            {tone ||
              "El análisis no identificó un tono de comunicación disponible."}
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Afinidad por categoría</Text>
          {affinities.length ? (
            affinities.map((item, index) => (
              <AffinityCard
                key={`${item.categoria}-${index}`}
                categoria={item.categoria}
                motivo={item.motivo}
              />
            ))
          ) : (
            <View style={styles.emptyCard}>
              <Text style={styles.description}>
                El backend no devolvió categorías de afinidad para este creador.
              </Text>
            </View>
          )}
          <Text style={styles.note}>
            Estas categorías son recomendaciones cualitativas. El backend actual
            no devuelve porcentajes de match por sector.
          </Text>
        </View>

        <View style={styles.infoBlock}>
          <Text style={styles.sectionTitle}>Intereses detectados</Text>
          {interests.length ? (
            <View style={styles.chips}>
              {interests.map((interest, index) => (
                <View key={`${interest}-${index}`} style={styles.chip}>
                  <Text style={styles.chipText}>{interest}</Text>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.description}>
              No hay intereses disponibles.
            </Text>
          )}
        </View>

        <View style={styles.actions}>
          <Pressable
            onPress={onContact}
            style={({ pressed }) => [
              styles.primaryButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.primaryButtonText}>Continuar a propuesta</Text>
          </Pressable>
          <Pressable
            onPress={onCancel}
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.secondaryButtonText}>Volver al reporte</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 32,
    gap: 20,
  },
  header: { gap: 8 },
  title: { fontSize: 28, fontWeight: "700", color: colors.text },
  subtitle: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  section: { gap: 12 },
  sectionTitle: { fontSize: 17, fontWeight: "700", color: colors.text },
  infoBlock: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 16,
    gap: 10,
  },
  description: { fontSize: 13, lineHeight: 19, color: colors.textMuted },
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 15,
  },
  categoryMark: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: colors.blueSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  categoryInitial: { fontSize: 17, fontWeight: "800", color: colors.blue },
  cardContent: { flex: 1, gap: 6 },
  cardName: { fontSize: 15, fontWeight: "700", color: colors.text },
  cardReason: { fontSize: 13, lineHeight: 19, color: colors.textMuted },
  emptyCard: {
    padding: 16,
    borderRadius: 14,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
  },
  note: { fontSize: 11, lineHeight: 16, color: colors.textMuted },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    backgroundColor: colors.blueSoft,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipText: { color: colors.blue, fontSize: 12, fontWeight: "600" },
  actions: { gap: 12, marginTop: "auto" },
  primaryButton: {
    minHeight: 56,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    backgroundColor: colors.green,
  },
  primaryButtonText: { color: colors.white, fontSize: 15, fontWeight: "700" },
  secondaryButton: {
    minHeight: 52,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    padding: 14,
    backgroundColor: colors.slate,
  },
  secondaryButtonText: { color: colors.white, fontSize: 14, fontWeight: "600" },
  pressed: { opacity: 0.82 },
});
