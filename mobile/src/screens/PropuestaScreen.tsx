import React from "react";
import { View, Text, StyleSheet, StatusBar } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { FileText } from "lucide-react-native";
import PrimaryButton from "../components/PrimaryButton";
import { colors } from "../theme";

type Props = { usuario: string; onHome: () => void };

/**
 * Estado honesto de la función: la API DDD actual de dev no implementa todavía
 * POST /api/propuestas. Esta pantalla no debe afirmar que una propuesta fue enviada.
 */
export default function PropuestaScreen({ usuario, onHome }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.content}>
        <View style={styles.center}>
          <View style={styles.iconWrap}>
            <FileText size={54} color={colors.blue} strokeWidth={1.7} />
          </View>
          <Text style={styles.title}>Propuestas próximamente</Text>
          <Text style={styles.desc}>
            El análisis de @{usuario} se completó. Sin embargo, el backend
            TrueMatch DDD de la rama dev todavía no dispone de un endpoint para
            registrar y enviar propuestas.
          </Text>
          <Text style={styles.note}>
            No se ha enviado ninguna solicitud al creador.
          </Text>
        </View>

        <PrimaryButton
          label="Volver al inicio"
          height={56}
          backgroundColor={colors.gray100}
          textColor={colors.blue}
          onPress={onHome}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.white },
  content: {
    flex: 1,
    paddingHorizontal: 32,
    paddingTop: 40,
    paddingBottom: 40,
  },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  iconWrap: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colors.blueSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    marginTop: 32,
    fontSize: 27,
    fontWeight: "700",
    color: colors.text,
    textAlign: "center",
  },
  desc: {
    marginTop: 16,
    fontSize: 15,
    lineHeight: 22,
    color: colors.textGray,
    textAlign: "center",
  },
  note: {
    marginTop: 14,
    fontSize: 13,
    fontWeight: "700",
    color: colors.textMuted,
    textAlign: "center",
  },
});
