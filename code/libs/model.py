''' Models with different neural network architectures '''
from __future__ import division
from libs.encode_cons import *
from libs.global_cons import *
import libs.util as util
import tensorflow as tf

def model(data, para, data_keys, net, train = False):
    '''
    Args:
        data: Tensor representing the model input
        para: Directory containing trainable parameters
        net: String representing the neural network architecture
        train: Bool representing whether the drop out should be used
        
    Returns:
        Tensor representing logits
    '''
    
    # Gated Convolutional Neural Network (GCNN) #
    if net == 'GCNN':        
        conv1 = tf.nn.conv2d(data, 
                            para['conv1_weights'],
                            strides = [1, 1, 1, 1],
                            padding = 'VALID')
        relu1 = tf.nn.relu(tf.nn.bias_add(conv1, para['conv1_biases']))
        pool1 = tf.nn.max_pool(relu1,
                               ksize = [1, 10, 1, 1],
                               strides = [1, 10, 1, 1],
                               padding = 'VALID')

        last_pool_shape = pool1.get_shape().as_list()
        motif_embed = tf.reshape(pool1, [last_pool_shape[0], last_pool_shape[1], last_pool_shape[3], last_pool_shape[2]])                
    
        num_layers = 3
        filter_size = filter_num
        filter_h = 5
        filter_w = last_pool_shape[3]
        block_size = 2

        '''
        motif_embed = tf.pad(motif_embed, [[0, 0], [filter_h -1, 0], [0, 0], [0, 0]], 'CONSTANT')
        with tf.variable_scope("motif") as scope:
            try:
                linear_W_1 = tf.get_variable("linear_W", (filter_h, filter_w, motif_embed.get_shape().as_list()[-1], filter_size), tf.float32, tf.random_normal_initializer(0.0, para['std_weights'], seed=SEED))
                linear_b_1 = tf.get_variable("linear_b", filter_size, tf.float32, tf.constant_initializer(0))

                gated_W_1 = tf.get_variable("gated_W", (filter_h, filter_w, motif_embed.get_shape().as_list()[-1], filter_size), tf.float32, tf.random_normal_initializer(0.0, para['std_weights'], seed=SEED))
                gated_b_1 = tf.get_variable("gated_b", filter_size, tf.float32, tf.constant_initializer(0))
            except ValueError:
                scope.reuse_variables()
                linear_W_1 = tf.get_variable("linear_W")
                linear_b_1 = tf.get_variable("linear_b")

                gated_W_1 = tf.get_variable("gated_W")
                gated_b_1 = tf.get_variable("gated_b")

            conv_w_1 = tf.nn.bias_add(tf.nn.conv2d(motif_embed, linear_W_1, strides = [1, 1, 1, 1], padding = "VALID"), linear_b_1)
            conv_v_1 = tf.nn.bias_add(tf.nn.conv2d(motif_embed, gated_W_1, strides = [1, 1, 1, 1], padding = "VALID"), gated_b_1)
            embed = conv_w_1 * tf.nn.sigmoid(conv_v_1)
            embed_shape = embed.get_shape().as_list()
            embed = tf.reshape(embed, [embed_shape[0], embed_shape[1], embed_shape[3], embed_shape[2]])
        h, res_input = embed, embed
        '''

        h, res_input = motif_embed, motif_embed

        for i in range(num_layers):
            h = tf.pad(h, [[0, 0], [filter_h - 1, 0], [0, 0], [0, 0]], 'CONSTANT')
            fanin_depth = h.get_shape().as_list()[-1]
            #filter_size = filter_size if i < num_layers-1 else 1
            filter_size = filter_size
            shape = (filter_h, filter_w, fanin_depth, filter_size)

            with tf.variable_scope("layer_%d"%i) as scope:
                try:    
                    linear_W = tf.get_variable("linear_W", shape, tf.float32, tf.random_normal_initializer(0.0, para['std_weights'], seed=SEED))
                    linear_b = tf.get_variable("linear_b", shape[-1], tf.float32, tf.constant_initializer(0))

                    gated_W = tf.get_variable("gated_W", shape, tf.float32, tf.random_normal_initializer(0.0, para['std_weights'], seed=SEED))
                    gated_b = tf.get_variable("gated_b", shape[-1], tf.float32, tf.constant_initializer(0))

                except ValueError:
                    scope.reuse_variables()
                    linear_W = tf.get_variable("linear_W")
                    linear_b = tf.get_variable("linear_b")

                    gated_W = tf.get_variable("gated_W")
                    gated_b = tf.get_variable("gated_b")

                conv_w = tf.nn.bias_add(tf.nn.conv2d(h, linear_W, strides = [1, 1, 1, 1], padding = 'VALID'), linear_b)
                conv_v = tf.nn.bias_add(tf.nn.conv2d(h, gated_W, strides = [1, 1, 1, 1], padding = 'VALID'), gated_b)
                h = conv_w * tf.nn.sigmoid(conv_v)

                if i == (num_layers - 1):
                    h = tf.nn.max_pool(h,
                                       ksize = [1, h.get_shape().as_list()[1], 1, 1],
                                       strides = [1, h.get_shape().as_list()[1], 1, 1],
                                       padding = 'VALID')

                h_shape = h.get_shape().as_list()
                h = tf.reshape(h, [h_shape[0], h_shape[1], h_shape[3], h_shape[2]])
                if (i + 1) % block_size == 0:
                    h += res_input
                    res_input = h


        h_shape = h.get_shape().as_list()
        fc_input = tf.reshape(h, [h_shape[0], h_shape[1] * h_shape[2] * h_shape[3]])
        hidden1 = tf.nn.relu(tf.matmul(fc_input, para['fc1_weights']) + para['fc1_biases'])
        if train:
            hidden1 = tf.nn.dropout(hidden1, para['drop_out_rate'], seed=SEED)

        return tf.matmul(hidden1, para['fc2_weights']) + para['fc2_biases']
    elif net == 'CNN':	
        ### CNN (convolutional neural network) ###
        for i, key in enumerate(data_keys):
            conv1 = tf.nn.conv2d(data[i], 
                                 para['conv1_weights'][key],
                                 strides = [1, 1, 1, 1],
                                 padding = 'VALID')
            relu1 = tf.nn.relu(tf.nn.bias_add(conv1, para['conv1_biases'][key]))
            pool1 = tf.nn.max_pool(relu1,
                                   ksize = [1, data[i].get_shape().as_list()[1] - filter_length + 1, 1, 1],
                                   strides = [1, 1, 1, 1],
                                   padding = 'VALID')

            # Fully connected layer #
            last_pool_shape = pool1.get_shape().as_list()
            if i == 0:
                fc_input = tf.reshape(pool1, [last_pool_shape[0], last_pool_shape[1] * last_pool_shape[2] * last_pool_shape[3]])
            else:
                fc_input = tf.concat([fc_input, tf.reshape(pool1, [last_pool_shape[0], last_pool_shape[1] * last_pool_shape[2] * last_pool_shape[3]])], 1)

        hidden1 = tf.nn.relu(tf.matmul(fc_input, para['fc1_weights']) + para['fc1_biases'])
        if train:
            hidden1 = tf.nn.dropout(hidden1, para['drop_out_rate'], seed=SEED)

        return tf.matmul(hidden1, para['fc2_weights']) + para['fc2_biases']
