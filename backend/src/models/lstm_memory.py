"""
Base LSTM Encoder-Decoder architecture for memory-augmented context processing.
This module provides the core LSTM components for processing sequences with memory augmentation.
"""
import torch
import torch.nn as nn
from typing import Tuple, Optional, Dict, Any
import numpy as np


class LSTMCell(nn.Module):
    """Custom LSTM cell implementation."""
    
    def __init__(self, input_size: int, hidden_size: int):
        super(LSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Input gate weights
        self.W_ii = nn.Parameter(torch.randn(hidden_size, input_size))
        self.W_hi = nn.Parameter(torch.randn(hidden_size, hidden_size))
        self.b_i = nn.Parameter(torch.randn(hidden_size))
        
        # Forget gate weights
        self.W_if = nn.Parameter(torch.randn(hidden_size, input_size))
        self.W_hf = nn.Parameter(torch.randn(hidden_size, hidden_size))
        self.b_f = nn.Parameter(torch.randn(hidden_size))
        
        # Cell gate weights
        self.W_ig = nn.Parameter(torch.randn(hidden_size, input_size))
        self.W_hg = nn.Parameter(torch.randn(hidden_size, hidden_size))
        self.b_g = nn.Parameter(torch.randn(hidden_size))
        
        # Output gate weights
        self.W_io = nn.Parameter(torch.randn(hidden_size, input_size))
        self.W_ho = nn.Parameter(torch.randn(hidden_size, hidden_size))
        self.b_o = nn.Parameter(torch.randn(hidden_size))
        
        self.reset_parameters()
    
    def reset_parameters(self):
        """Initialize parameters with Xavier uniform."""
        std = 1.0 / np.sqrt(self.hidden_size)
        for param in self.parameters():
            nn.init.uniform_(param, -std, std)
    
    def forward(self, input_tensor: torch.Tensor, hidden: Tuple[torch.Tensor, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through LSTM cell.
        
        Args:
            input_tensor: Input tensor of shape (batch_size, input_size)
            hidden: Tuple of (hidden_state, cell_state) each of shape (batch_size, hidden_size)
        
        Returns:
            Tuple of (new_hidden_state, new_cell_state)
        """
        h_prev, c_prev = hidden
        
        # Input gate
        i_t = torch.sigmoid(torch.matmul(input_tensor, self.W_ii.t()) + 
                           torch.matmul(h_prev, self.W_hi.t()) + self.b_i)
        
        # Forget gate
        f_t = torch.sigmoid(torch.matmul(input_tensor, self.W_if.t()) + 
                           torch.matmul(h_prev, self.W_hf.t()) + self.b_f)
        
        # Cell gate
        g_t = torch.tanh(torch.matmul(input_tensor, self.W_ig.t()) + 
                        torch.matmul(h_prev, self.W_hg.t()) + self.b_g)
        
        # New cell state
        c_t = f_t * c_prev + i_t * g_t
        
        # Output gate
        o_t = torch.sigmoid(torch.matmul(input_tensor, self.W_io.t()) + 
                           torch.matmul(h_prev, self.W_ho.t()) + self.b_o)
        
        # New hidden state
        h_t = o_t * torch.tanh(c_t)
        
        return h_t, c_t


class LSTMEncoder(nn.Module):
    """LSTM Encoder for processing input sequences."""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1, dropout: float = 0.0):
        super(LSTMEncoder, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm_cells = nn.ModuleList([
            LSTMCell(input_size if i == 0 else hidden_size, hidden_size)
            for i in range(num_layers)
        ])
        
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
    
    def forward(self, input_sequence: torch.Tensor, hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Encode input sequence.
        
        Args:
            input_sequence: Input tensor of shape (sequence_length, batch_size, input_size)
            hidden: Optional initial hidden state tuple
        
        Returns:
            Tuple of (output_sequence, final_hidden_state)
        """
        batch_size = input_sequence.size(1)
        device = input_sequence.device
        
        if hidden is None:
            h = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
            c = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        else:
            h, c = hidden
        
        outputs = []
        seq_len = input_sequence.size(0)
        
        for t in range(seq_len):
            x_t = input_sequence[t]
            layer_input = x_t
            
            for layer_idx, lstm_cell in enumerate(self.lstm_cells):
                h_layer = h[layer_idx]
                c_layer = c[layer_idx]
                h_new, c_new = lstm_cell(layer_input, (h_layer, c_layer))
                
                h[layer_idx] = h_new
                c[layer_idx] = c_new
                
                layer_input = self.dropout(h_new)
            
            outputs.append(layer_input)
        
        output_sequence = torch.stack(outputs, dim=0)
        final_hidden = (h, c)
        
        return output_sequence, final_hidden


class LSTMDecoder(nn.Module):
    """LSTM Decoder for generating output sequences."""
    
    def __init__(self, hidden_size: int, output_size: int, num_layers: int = 1, dropout: float = 0.0):
        super(LSTMDecoder, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        self.lstm_cells = nn.ModuleList([
            LSTMCell(hidden_size if i == 0 else hidden_size, hidden_size)
            for i in range(num_layers)
        ])
        
        self.output_projection = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
    
    def forward(self, hidden: Tuple[torch.Tensor, torch.Tensor], max_length: int = 1, 
                input_tensor: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Decode from hidden state.
        
        Args:
            hidden: Hidden state tuple from encoder
            max_length: Maximum sequence length to generate
            input_tensor: Optional input tensor for first step
        
        Returns:
            Output tensor of shape (max_length, batch_size, output_size)
        """
        h, c = hidden
        batch_size = h.size(1)
        device = h.device
        
        outputs = []
        
        # Use input_tensor if provided, otherwise use zero tensor
        if input_tensor is None:
            decoder_input = torch.zeros(batch_size, self.hidden_size, device=device)
        else:
            decoder_input = input_tensor
        
        for t in range(max_length):
            layer_input = decoder_input
            
            for layer_idx, lstm_cell in enumerate(self.lstm_cells):
                h_layer = h[layer_idx]
                c_layer = c[layer_idx]
                h_new, c_new = lstm_cell(layer_input, (h_layer, c_layer))
                
                h[layer_idx] = h_new
                c[layer_idx] = c_new
                
                layer_input = self.dropout(h_new)
            
            # Project to output space
            output = self.output_projection(layer_input)
            outputs.append(output)
            
            # Use output as next input (or could use teacher forcing)
            decoder_input = layer_input
        
        return torch.stack(outputs, dim=0)


class MemoryAugmentedLSTM(nn.Module):
    """
    Memory-Augmented LSTM Encoder-Decoder.
    This model processes sequences with memory augmentation from STM and LTM.
    """
    
    def __init__(self, input_size: int, hidden_size: int, output_size: int, 
                 num_layers: int = 2, dropout: float = 0.1):
        super(MemoryAugmentedLSTM, self).__init__()
        self.hidden_size = hidden_size
        
        # Encoder processes input sequence
        self.encoder = LSTMEncoder(input_size, hidden_size, num_layers, dropout)
        
        # Decoder generates output
        self.decoder = LSTMDecoder(hidden_size, output_size, num_layers, dropout)
        
        # Memory fusion layer to combine STM and LTM with input
        self.memory_fusion = nn.Linear(hidden_size * 3, hidden_size)  # input + STM + LTM
    
    def forward(self, input_sequence: torch.Tensor, 
                stm_context: Optional[torch.Tensor] = None,
                ltm_context: Optional[torch.Tensor] = None,
                hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass with memory augmentation.
        
        Args:
            input_sequence: Input tensor (seq_len, batch, input_size)
            stm_context: Short-term memory context (batch, hidden_size)
            ltm_context: Long-term memory context (batch, hidden_size)
            hidden: Optional initial hidden state
        
        Returns:
            Dictionary with 'output', 'hidden', and 'context' keys
        """
        # Encode input sequence
        encoded_output, encoder_hidden = self.encoder(input_sequence, hidden)
        
        # Get final encoded representation
        final_encoded = encoded_output[-1]  # (batch, hidden_size)
        
        # Fuse memory contexts if provided
        if stm_context is not None and ltm_context is not None:
            # Concatenate input, STM, and LTM
            fused_input = torch.cat([final_encoded, stm_context, ltm_context], dim=-1)
            # Project to hidden size
            memory_augmented = self.memory_fusion(fused_input)
        elif stm_context is not None:
            fused_input = torch.cat([final_encoded, stm_context, torch.zeros_like(stm_context)], dim=-1)
            memory_augmented = self.memory_fusion(fused_input)
        elif ltm_context is not None:
            fused_input = torch.cat([final_encoded, torch.zeros_like(final_encoded), ltm_context], dim=-1)
            memory_augmented = self.memory_fusion(fused_input)
        else:
            memory_augmented = final_encoded
        
        # Decode from memory-augmented hidden state
        # For context processing, we typically want a single output representation
        decoder_output = self.decoder(encoder_hidden, max_length=1, input_tensor=memory_augmented)
        
        return {
            'output': decoder_output[0],  # (batch, output_size)
            'hidden': encoder_hidden,
            'context': memory_augmented  # (batch, hidden_size)
        }
    
    def get_context_representation(self, input_text: str, stm_summary: str, ltm_summary: str) -> torch.Tensor:
        """
        Get context representation for text input (simplified version for inference).
        In practice, this would use tokenization and embedding layers.
        
        Args:
            input_text: Current input text
            stm_summary: STM summary
            ltm_summary: LTM summary
        
        Returns:
            Context representation tensor
        """
        # This is a placeholder - in practice, you'd tokenize and embed
        # For now, return a zero tensor as the actual processing happens in the service layer
        return torch.zeros(1, self.hidden_size)

