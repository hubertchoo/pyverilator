import os
import pyverilator

# setup build directory and cd to it
build_dir = os.path.join(os.path.dirname(__file__), 'build', os.path.basename(__file__))
os.makedirs(build_dir, exist_ok = True)
os.chdir(build_dir)

test_verilog = '''
    module latencyInsensitiveAdder (
    input   logic           clk,
    input   logic           rst_n,

    // Source Interface (input operands)
    input   logic [31:0]    in_a,
    input   logic [31:0]    in_b,
    input   logic           in_valid,
    output  logic           in_ready,

    // Sink Interface (output result)
    output  logic [31:0]    sum,
    output  logic           out_valid,
    input   logic           out_ready
);

    logic [31:0] sum_reg;
    logic        compute_done_state;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            sum_reg            <= 32'd0;
            compute_done_state <= 1'b0;
        end
        else begin
            if (in_valid && in_ready) begin
                sum_reg            <= in_a + in_b;
                compute_done_state <= 1'b1;
            end
            else if (out_valid && out_ready) begin
                sum_reg            <= 32'd0;
                compute_done_state <= 1'b0;
            end
        end
    end

    always_comb begin
        if (compute_done_state) begin
            in_ready  = 1'b0;
            out_valid = 1'b1;
        end
        else begin
            in_ready  = 1'b1;
            out_valid = 1'b0;
        end
    end

    assign sum = sum_reg;

endmodule
'''

with open('adder.sv', 'w') as f:
    f.write(test_verilog)

sim = pyverilator.PyVerilator.build('adder.sv')

# start gtkwave to view the waveforms as they are made
# sim.start_gtkwave()

# add all the io and internal signals to gtkwave
# sim.send_to_gtkwave(sim.io)
# sim.send_to_gtkwave(sim.internals)

def reset_module():
    sim.io.rst_n = 0
    sim.clock.tick()
    sim.io.rst_n = 1

def add_with_latency_insensitive_interface(in_a, in_b):
    # Set input values
    sim.io.in_a = in_a
    sim.io.in_b = in_b
    sim.io.in_valid = 1

    # Step the clock until the output is valid
    while not sim.io.out_valid:
        sim.clock.tick()

    # Now the output is valid, return the sum
    result = sim.io.sum

    # Clear the valid signal for future operations
    sim.io.in_valid = 0
    sim.io.out_ready = 1
    sim.clock.tick()

    return result

def latency_insensitive_interface(inputs, expected_outputs):
    # Set the input values based on the provided dictionary
    for input_name, value in inputs.items():
        setattr(sim.io, input_name, value)

    # Set the in_valid signal to 1 (assuming the interface has an in_valid signal)
    sim.io.in_valid = 1

    # Step the clock until the output is valid (assuming there's an out_valid signal)
    while not sim.io.out_valid:
        sim.clock.tick()

    # Perform the assertion checks for the expected outputs
    for output_name, expected_value in expected_outputs.items():
        actual_value = getattr(sim.io, output_name)
        assert actual_value == expected_value, f"Assertion failed: {output_name} = {actual_value}, expected {expected_value}"
        print(inputs, expected_outputs)
        print()

    # Clear the in_valid signal and set out_ready for future operations
    sim.io.in_valid = 0
    sim.io.out_ready = 1
    sim.clock.tick()

reset_module()

print(int(add_with_latency_insensitive_interface(30, 40)))
print(int(add_with_latency_insensitive_interface(10, 15)))

# assertion pass
latency_insensitive_interface( inputs=
                                    {'in_a' : 5,
                                    'in_b' : 16},
                               expected_outputs =
                                    {'sum' : 21} )

# assertion fail
latency_insensitive_interface( inputs=
                                    {'in_a' : 5,
                                    'in_b' : 16},
                               expected_outputs =
                                    {'sum' : 5} )
