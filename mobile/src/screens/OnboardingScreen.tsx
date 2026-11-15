import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import PrimaryButton from '../components/PrimaryButton';
import { colors } from '../theme';

type Props = { onSubmit: (usuario: string) => void };

export default function OnboardingScreen({ onSubmit }: Props) {
  const [usuario, setUsuario] = useState('');
  const limpio = usuario.trim().replace(/^@/, '');

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.content}>
          <Text style={styles.title}>Analiza al influencer ideal para tu campaña</Text>

          <View style={styles.form}>
            <Text style={styles.help}>
              Ingresa el usuario para validar su audiencia y personalidad
            </Text>
            <View style={styles.group}>
              <Text style={styles.label}>Usuario de redes sociales</Text>
              <TextInput
                value={usuario}
                onChangeText={setUsuario}
                placeholder="@danielvalencia365"
                placeholderTextColor={colors.placeholder}
                autoCapitalize="none"
                autoCorrect={false}
                style={styles.input}
              />
            </View>
          </View>

          <View style={styles.flex} />

          <PrimaryButton
            label="Cargar Datos"
            disabled={!limpio}
            onPress={() => onSubmit(limpio)}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.white },
  flex: { flex: 1 },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 40,
    paddingBottom: 40,
    gap: 32,
  },
  title: { fontSize: 28, fontWeight: '700', color: colors.text },
  form: { gap: 24 },
  help: { fontSize: 14, color: colors.textMuted },
  group: { gap: 8 },
  label: { fontSize: 14, fontWeight: '600', color: colors.textSoft },
  input: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: colors.text,
  },
});