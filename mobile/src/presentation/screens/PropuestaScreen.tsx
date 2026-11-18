import React from 'react';
import { View, Text, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { User, Check } from 'lucide-react-native';
import PrimaryButton from '../components/PrimaryButton';
import { colors } from '../theme';

type Props = { usuario: string; onHome: () => void };

export default function PropuestaScreen({ usuario, onHome }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.content}>
        <View style={styles.center}>
          <View style={styles.avatarWrap}>
            <View style={styles.avatar}>
              <User size={52} color={colors.placeholder} strokeWidth={1.5} />
            </View>
            <View style={styles.badge}>
              <Check size={16} color={colors.white} strokeWidth={3} />
            </View>
          </View>

          <Text style={styles.title}>¡Propuesta Enviada!</Text>
          <Text style={styles.desc}>
            Tu solicitud de colaboración ha sido entregada a @{usuario}. El creador revisará los
            detalles de tu campaña y se pondrá en contacto pronto.
          </Text>
        </View>

        <PrimaryButton
          label="Volver al Inicio"
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
  content: { flex: 1, paddingHorizontal: 32, paddingTop: 40, paddingBottom: 40 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  avatarWrap: { width: 120, height: 120 },
  avatar: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colors.border,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge: {
    position: 'absolute',
    right: 4,
    bottom: 4,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.green,
    borderWidth: 2,
    borderColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    marginTop: 32,
    fontSize: 28,
    fontWeight: '700',
    color: colors.text,
    textAlign: 'center',
  },
  desc: {
    marginTop: 16,
    fontSize: 15,
    color: colors.textGray,
    textAlign: 'center',
  },
});