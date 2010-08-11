(* Nmag micromagnetic simulator
 * Copyright (C) 2010 University of Southampton
 * Hans Fangohr, Thomas Fischbacher, Matteo Franchin and others
 *
 * WEB:     http://nmag.soton.ac.uk
 * CONTACT: nmag@soton.ac.uk
 *
 * AUTHOR(S) OF THIS FILE: Matteo Franchin
 * LICENSE: GNU General Public License 2.0
 *          (see <http://www.gnu.org/licenses/>)
 *
 * This module defines the datastructures storing simplex information in
 * a mesh. It also contains various routines to build and retrieve such
 * information.
 *
 *)

open Base.Ba

(*
     (*
        Circum-Circle and In-Circle.

        They are needed at least for the simplex quality test, but
        keeping track of those allows us to do Delaunay triangulation
        in D dimensions without having to refer to D+1 dimensions.
      *)
     mutable ms_cc_midpoint: float array;
     mutable ms_ic_midpoint: float array;
     mutable ms_cc_radius: float;
     mutable ms_ic_radius: float;

     (* Extended point coordinates as a matrix (last coordinate =1) *)
     mutable ms_ext_point_coords: float array array option;                              (* this variables are now mutable in order to update *)
     (* The inverse provides a concise way to get all the cofactors. *)                  (* them when we call the function scale_node_positions!! *)
     (* Also, the j'th row of the inverse is just the j'th face equation! *)
     mutable ms_inv_ext_point_coords: float array array option;
     mutable ms_point_coords_det: float;
*)

type t = {
  msd_mesh0: Mesh0.t;
  (** The mesh to which this simplex info is attached to *)

  mutable msd_ext_point_coords: F.array3 Deferred.t;
  (** Point matrices *)

  mutable msd_inv_ext_point_coords: F.array3 Deferred.t;
  (** Inverse point matrices *)

  mutable msd_point_coords_det: F.array1 Deferred.t;
  (** Determinants of point matrices *)

  mutable msd_ic_cc_data: F.array2 Deferred.t;
  (** incircle and circumcircle midpoints (d*2 floats)
      and radii (1*2 floats) *)
}

let my_build_point_matrices m0 =
  let d = Mesh0.get_nr_dims m0 in
  let n = Mesh0.get_nr_simplices m0 in
  let ba = F.create3 n (d + 1) (d + 1) in
  let () =
    F.iter32 ba
      (fun nr_spx matrix ->
         F.iter21 matrix
           (fun nr_row row ->
              if nr_row = d
              then Bigarray.Array1.fill row 1.0
              else
                F.set_all1 row
                  (fun nr_col ->
                     let point_coords = Mesh0.get_simplex_point m0 nr_spx nr_col
                     in point_coords.{nr_row})))
  in ba

let my_build_inv_point_matrices m0 deferred_point_matrices =
  let d = Mesh0.get_nr_dims m0 in
  let n = Mesh0.get_nr_simplices m0 in
  let compute_det_and_inv = Snippets.det_and_inv (d + 1) in
  let mxs = Deferred.get deferred_point_matrices in
  let ba = F.create3 n (d + 1) (d + 1) in
  let () =
    F.iter32 ba
      (fun nr_spx dst_matrix ->
         let src_matrix = F.to_ml2 (F.slice32 mxs nr_spx) in
         let det, ml_inv_matrix = compute_det_and_inv src_matrix in
           F.set_all2 dst_matrix (fun i1 i2 -> ml_inv_matrix.(i1).(i2)))
  in ba

let init m0 =
  let d = Mesh0.get_nr_dims m0 in
  let dd = d + 1 in
  let n = Mesh0.get_nr_simplices m0 in
  let fa1_creator () = F.create1 n in
  let fa2_creator () = F.create2 n dd in

  let deferred_point_matrices =
    Deferred.init
      ~creator:(fun () -> my_build_point_matrices m0)
      "ext_point_coords"
  in
  let deferred_inv_point_matrices =
    Deferred.init
      ~creator:(fun () -> my_build_inv_point_matrices m0 deferred_point_matrices)
      "inv_ext_point_coords"
  in
  let ic_cc_data = Deferred.init ~creator:fa2_creator "ic_cc_data" in
  let point_coords_det = Deferred.init ~creator:fa1_creator "point_coords_det"
  in
    { msd_mesh0 = m0;
      msd_ext_point_coords = deferred_point_matrices;
      msd_inv_ext_point_coords = deferred_inv_point_matrices;
      msd_point_coords_det = point_coords_det;
      msd_ic_cc_data = ic_cc_data; }

(** Get the point matrix for the given simplex. *)
let get_point_matrix sx_data sx_id =
  let ba3 = Deferred.get sx_data.msd_ext_point_coords in
    Bigarray.Array3.slice_left_2 ba3 sx_id

(** Get the inverse point matrix for the given simplex. *)
let get_inv_point_matrix sx_data sx_id =
  let ba3 = Deferred.get sx_data.msd_ext_point_coords in
    Bigarray.Array3.slice_left_2 ba3 sx_id

(** Get the n-th row of the inverse point matrix for the given simplex.
    That corresponds to retrieve the coefficients of the equation of the n-th
    face of the simplex. *)
let get_face_eqn sx_data sx_id n =
  let mx = get_inv_point_matrix sx_data sx_id in
    Bigarray.Array2.slice_left mx n

let dummy = init Mesh0.dummy