/**
 * Main App component for RuneScape Smart Item Search
 */

import React from 'react';
import {SafeAreaView, StatusBar, StyleSheet} from 'react-native';
import SearchScreen from './SearchScreen.example';

const App: React.FC = () => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <SearchScreen />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});

export default App;

