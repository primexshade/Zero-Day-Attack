"""
Variational Autoencoder (VAE) for anomaly detection
Detects deviations from normal network behavior
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from typing import Tuple, Dict, Any
import os

from .base_model import BaseModel


class VariationalAutoencoder(BaseModel):
    """VAE model for unsupervised anomaly detection"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize VAE model"""
        super().__init__(name="VariationalAutoencoder", config=config)
        self.config = config or {}
        self.encoder = None
        self.decoder = None
        
    def build(self) -> None:
        """Build VAE architecture"""
        ae_config = self.config.get("autoencoder", {})
        input_dim = ae_config.get("input_dim", 50)
        latent_dim = ae_config.get("latent_dim", 16)
        encoder_layers = ae_config.get("encoder_layers", [128, 64])
        decoder_layers = ae_config.get("decoder_layers", [64, 128])
        dropout = ae_config.get("dropout", 0.2)
        
        # Encoder
        encoder_inputs = keras.Input(shape=(input_dim,))
        x = encoder_inputs
        
        for units in encoder_layers:
            x = layers.Dense(units, activation="relu")(x)
            x = layers.Dropout(dropout)(x)
            x = layers.BatchNormalization()(x)
        
        # Latent space
        z_mean = layers.Dense(latent_dim, name="z_mean")(x)
        z_log_var = layers.Dense(latent_dim, name="z_log_var")(x)
        
        # Sampling layer
        z = layers.Lambda(self._sampling, name="z")([z_mean, z_log_var])
        
        self.encoder = Model(encoder_inputs, [z_mean, z_log_var, z], name="encoder")
        
        # Decoder
        latent_inputs = keras.Input(shape=(latent_dim,))
        x = latent_inputs
        
        for units in decoder_layers:
            x = layers.Dense(units, activation="relu")(x)
            x = layers.Dropout(dropout)(x)
            x = layers.BatchNormalization()(x)
        
        decoder_outputs = layers.Dense(input_dim, activation="sigmoid")(x)
        self.decoder = Model(latent_inputs, decoder_outputs, name="decoder")
        
        # Full VAE
        outputs = self.decoder(self.encoder(encoder_inputs)[2])
        self.model = Model(encoder_inputs, outputs, name="VAE")
        
        # Custom loss (reconstruction + KL divergence)
        reconstruction_loss = keras.losses.mse(encoder_inputs, outputs)
        reconstruction_loss *= input_dim
        kl_loss = 1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var)
        kl_loss = tf.reduce_mean(tf.reduce_sum(kl_loss, axis=1)) * -0.5
        vae_loss = tf.reduce_mean(reconstruction_loss + kl_loss)
        
        self.model.add_loss(vae_loss)
        self.model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001))

    def _sampling(self, args: Tuple) -> np.ndarray:
        """Reparameterization trick"""
        z_mean, z_log_var = args
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.random.normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon

    def train(self, X_train: np.ndarray, y_train: np.ndarray = None,
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> Dict:
        """Train VAE (unsupervised)"""
        if self.model is None:
            self.build()
        
        training_config = self.config.get("training", {})
        batch_size = training_config.get("batch_size", 32)
        epochs = training_config.get("num_epochs", 100)
        patience = training_config.get("early_stopping_patience", 10)
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="loss",
                patience=patience,
                restore_best_weights=True
            )
        ]
        
        history = self.model.fit(
            X_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_data=(X_val, None) if X_val is not None else None,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        self.history = history.history
        return self.history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Reconstruct input and compute anomaly score"""
        if self.model is None:
            raise RuntimeError("Model not built. Call build() first.")
        
        reconstruction = self.model.predict(X, verbose=0)
        # Anomaly score: reconstruction error
        anomaly_score = np.mean(np.square(X - reconstruction), axis=1)
        return anomaly_score

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray = None) -> Dict[str, float]:
        """Evaluate VAE"""
        if self.model is None:
            raise RuntimeError("Model not built. Call build() first.")
        
        loss = self.model.evaluate(X_test, verbose=0)
        return {"reconstruction_loss": float(loss)}

    def save(self, filepath: str) -> None:
        """Save model"""
        if self.model is None:
            raise RuntimeError("No model to save.")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        
    def load(self, filepath: str) -> None:
        """Load model"""
        self.model = keras.models.load_model(filepath)
        self.is_trained = True
